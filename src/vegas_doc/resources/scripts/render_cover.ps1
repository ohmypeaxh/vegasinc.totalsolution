param(
    [Parameter(Mandatory = $true)]
    [string]$RequestPath
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)
$OutputEncoding = [Console]::OutputEncoding
$script:FoundTokens = @{}
$CentimetreToPoint = 28.3464566929

Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;

public static class VegasWindowProcess
{
    [DllImport("user32.dll")]
    public static extern uint GetWindowThreadProcessId(IntPtr windowHandle, out uint processId);
}
"@

function Get-ComProperty {
    param([object]$ComObject, [string]$Name, [object[]]$Arguments = @())
    if ($null -eq $ComObject) {
        throw "Excel COM property '$Name' has no target object."
    }
    try {
        $result = $ComObject.GetType().InvokeMember(
            $Name,
            [System.Reflection.BindingFlags]::GetProperty,
            $null,
            $ComObject,
            $Arguments
        )
    }
    catch {
        throw "Failed to read Excel COM property '$Name': $($_.Exception.Message)"
    }
    Write-Output -NoEnumerate $result
}

function Set-ComProperty {
    param([object]$ComObject, [string]$Name, [object]$Value)
    if ($null -eq $ComObject) {
        throw "Excel COM property '$Name' has no target object."
    }
    try {
        [void]$ComObject.GetType().InvokeMember(
            $Name,
            [System.Reflection.BindingFlags]::SetProperty,
            $null,
            $ComObject,
            @($Value)
        )
    }
    catch {
        throw "Failed to write Excel COM property '$Name': $($_.Exception.Message)"
    }
}

function Invoke-ComMethod {
    param([object]$ComObject, [string]$Name, [object[]]$Arguments = @())
    if ($null -eq $ComObject) {
        throw "Excel COM method '$Name' has no target object."
    }
    try {
        $result = $ComObject.GetType().InvokeMember(
            $Name,
            [System.Reflection.BindingFlags]::InvokeMethod,
            $null,
            $ComObject,
            $Arguments
        )
    }
    catch {
        throw "Failed to call Excel COM method '$Name': $($_.Exception.Message)"
    }
    Write-Output -NoEnumerate $result
}

function Release-ComObject {
    param([object]$ComObject)
    if ($null -ne $ComObject -and [Runtime.InteropServices.Marshal]::IsComObject($ComObject)) {
        [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($ComObject)
    }
}

function Get-ComItem {
    param([object]$Collection, [object[]]$Arguments, [string]$Context)
    $errors = @()
    foreach ($memberName in @("Item", "_Default", "")) {
        try {
            return Get-ComProperty $Collection $memberName $Arguments
        }
        catch {
            $errors += $_.Exception.Message
        }
    }
    throw "Failed to access Excel COM indexer '$Context': $($errors -join ' | ')"
}

function Get-ShapeText {
    param([object]$Shape)
    $textFrame = $null
    $textRange = $null
    try {
        $textFrame = Get-ComProperty $Shape "TextFrame2"
        if ((Get-ComProperty $textFrame "HasText") -ne 0) {
            $textRange = Get-ComProperty $textFrame "TextRange"
            return [string](Get-ComProperty $textRange "Text")
        }
    }
    catch {}
    finally {
        Release-ComObject $textRange
        Release-ComObject $textFrame
    }
    return ""
}

function Set-ShapeText {
    param([object]$Shape, [string]$Text)
    $textFrame = $null
    $textRange = $null
    try {
        $textFrame = Get-ComProperty $Shape "TextFrame2"
        $textRange = Get-ComProperty $textFrame "TextRange"
        Set-ComProperty $textRange "Text" $Text
    }
    finally {
        Release-ComObject $textRange
        Release-ComObject $textFrame
    }
}

function Add-CentredLogo {
    param(
        [object]$Sheet,
        [double]$AnchorLeft,
        [double]$AnchorTop,
        [double]$AnchorWidth,
        [double]$AnchorHeight,
        [string]$LogoPath,
        [object]$Placement
    )
    $shapes = $null
    $picture = $null
    try {
        $shapes = Get-ComProperty $Sheet "Shapes"
        $picture = Invoke-ComMethod $shapes "AddPicture" @($LogoPath, $false, $true, 0, 0, -1, -1)
        Set-ComProperty $picture "LockAspectRatio" -1
        $points = [double]$Placement.centimetres * $CentimetreToPoint
        if ([string]$Placement.dimension -eq "height") {
            Set-ComProperty $picture "Height" $points
        }
        else {
            Set-ComProperty $picture "Width" $points
        }
        $pictureWidth = [double](Get-ComProperty $picture "Width")
        $pictureHeight = [double](Get-ComProperty $picture "Height")
        Set-ComProperty $picture "Left" ($AnchorLeft + (($AnchorWidth - $pictureWidth) / 2))
        Set-ComProperty $picture "Top" ($AnchorTop + (($AnchorHeight - $pictureHeight) / 2))
    }
    finally {
        Release-ComObject $picture
        Release-ComObject $shapes
    }
}

function Update-SheetPlaceholders {
    param([object]$Sheet, [object]$Request)

    $originalShapes = $null
    $shapesToProcess = New-Object 'System.Collections.Generic.List[object]'
    try {
        $originalShapes = Get-ComProperty $Sheet "Shapes"
        foreach ($shape in $originalShapes) {
            [void]$shapesToProcess.Add($shape)
        }
    }
    finally {
        Release-ComObject $originalShapes
    }

    try {
        foreach ($shape in $shapesToProcess) {
            $text = Get-ShapeText $shape
            if (-not $text) {
                continue
            }
            $rendered = $text
            foreach ($property in $Request.replacements.PSObject.Properties) {
                $token = [string]$property.Name
                if ($rendered.Contains($token)) {
                    $script:FoundTokens[$token] = $true
                    $rendered = $rendered.Replace($token, [string]$property.Value)
                }
            }
            foreach ($placement in $Request.logo_placements) {
                $token = [string]$placement.token
                if (-not $rendered.Contains($token)) {
                    continue
                }
                $script:FoundTokens[$token] = $true
                $rendered = $rendered.Replace($token, "")
                Add-CentredLogo `
                    $Sheet `
                    ([double](Get-ComProperty $shape "Left")) `
                    ([double](Get-ComProperty $shape "Top")) `
                    ([double](Get-ComProperty $shape "Width")) `
                    ([double](Get-ComProperty $shape "Height")) `
                    $Request.logo_path `
                    $placement
            }
            if ($rendered -ne $text) {
                Set-ShapeText $shape $rendered
            }
        }
    }
    finally {
        foreach ($shape in $shapesToProcess) {
            Release-ComObject $shape
        }
    }

    $used = $null
    $rows = $null
    $columns = $null
    $cells = $null
    $values = $null
    try {
        $used = Get-ComProperty $Sheet "UsedRange"
        $rows = Get-ComProperty $used "Rows"
        $columns = Get-ComProperty $used "Columns"
        $cells = Get-ComProperty $used "Cells"
        $values = Get-ComProperty $used "Value2"
        $rowCount = [int](Get-ComProperty $rows "Count")
        $columnCount = [int](Get-ComProperty $columns "Count")
        for ($row = 1; $row -le $rowCount; $row++) {
            for ($column = 1; $column -le $columnCount; $column++) {
                $cell = $null
                $anchor = $null
                try {
                    if ($values -is [Array]) {
                        $value = $values.GetValue($row, $column)
                    }
                    elseif ($row -eq 1 -and $column -eq 1) {
                        $value = $values
                    }
                    else {
                        $value = $null
                    }
                    if ($value -isnot [string]) {
                        continue
                    }
                    $rendered = [string]$value
                    foreach ($property in $Request.replacements.PSObject.Properties) {
                        $token = [string]$property.Name
                        if ($rendered.Contains($token)) {
                            $script:FoundTokens[$token] = $true
                            $rendered = $rendered.Replace($token, [string]$property.Value)
                        }
                    }
                    $containsLogo = $false
                    foreach ($placement in $Request.logo_placements) {
                        if ($rendered.Contains([string]$placement.token)) {
                            $containsLogo = $true
                            break
                        }
                    }
                    if ($rendered -eq $value -and -not $containsLogo) {
                        continue
                    }
                    $cell = Get-ComItem $cells @($row, $column) "UsedRange.Cells[$row,$column]"
                    foreach ($placement in $Request.logo_placements) {
                        $token = [string]$placement.token
                        if (-not $rendered.Contains($token)) {
                            continue
                        }
                        $script:FoundTokens[$token] = $true
                        $rendered = $rendered.Replace($token, "")
                        if ([bool](Get-ComProperty $cell "MergeCells")) {
                            $anchor = Get-ComProperty $cell "MergeArea"
                        }
                        else {
                            $anchor = $cell
                        }
                        Add-CentredLogo `
                            $Sheet `
                            ([double](Get-ComProperty $anchor "Left")) `
                            ([double](Get-ComProperty $anchor "Top")) `
                            ([double](Get-ComProperty $anchor "Width")) `
                            ([double](Get-ComProperty $anchor "Height")) `
                            $Request.logo_path `
                            $placement
                    }
                    if ($rendered -ne $value) {
                        Set-ComProperty $cell "Value2" $rendered
                    }
                }
                finally {
                    if ($null -ne $anchor -and -not [object]::ReferenceEquals($anchor, $cell)) {
                        Release-ComObject $anchor
                    }
                    Release-ComObject $cell
                }
            }
        }
    }
    finally {
        Release-ComObject $cells
        Release-ComObject $columns
        Release-ComObject $rows
        Release-ComObject $used
    }

}

$excel = $null
$workbook = $null
$excelProcessId = [uint32]0
$primaryError = $null
$cleanupError = $null
try {
    $request = Get-Content -LiteralPath $RequestPath -Raw -Encoding UTF8 | ConvertFrom-Json
    try {
        $excel = New-Object -ComObject Excel.Application
    }
    catch {
        throw "Microsoft Excel could not be started. Install Microsoft Excel to use Cover Generator."
    }
    Set-ComProperty $excel "Visible" $false
    Set-ComProperty $excel "DisplayAlerts" $false
    Set-ComProperty $excel "ScreenUpdating" $false
    $excelWindowHandle = [IntPtr][long](Get-ComProperty $excel "Hwnd")
    [void][VegasWindowProcess]::GetWindowThreadProcessId($excelWindowHandle, [ref]$excelProcessId)

    $workbooks = $null
    try {
        $workbooks = Get-ComProperty $excel "Workbooks"
        $workbook = Invoke-ComMethod $workbooks "Open" @([string]$request.template_path, 0, $true)
    }
    finally {
        Release-ComObject $workbooks
    }

    $worksheets = $null
    try {
        $worksheets = Get-ComProperty $workbook "Worksheets"
        foreach ($export in $request.sheet_exports) {
            $sheet = $null
            try {
                try {
                    $sheet = Get-ComItem $worksheets @([string]$export.sheet_name) "Worksheet[$($export.sheet_name)]"
                }
                catch {
                    throw "Required worksheet '$($export.sheet_name)' was not found in the Excel template."
                }
                Update-SheetPlaceholders $sheet $request
            }
            finally {
                Release-ComObject $sheet
            }
        }

        $missing = @($request.required_tokens | Where-Object { -not $script:FoundTokens.ContainsKey([string]$_) })
        if ($missing.Count -gt 0) {
            throw "Required placeholders were not found in the Excel template: $($missing -join ', ')"
        }

        [void](Invoke-ComMethod $excel "CalculateFull")
        foreach ($export in $request.sheet_exports) {
            $sheet = $null
            $pageSetup = $null
            try {
                $sheet = Get-ComItem $worksheets @([string]$export.sheet_name) "Worksheet[$($export.sheet_name)]"
                $pageSetup = Get-ComProperty $sheet "PageSetup"
                Set-ComProperty $pageSetup "Zoom" $false
                Set-ComProperty $pageSetup "FitToPagesWide" 1
                Set-ComProperty $pageSetup "FitToPagesTall" 1
                [void](Invoke-ComMethod $sheet "ExportAsFixedFormat" @(0, [string]$export.output_path, 0, $true, $false))
            }
            finally {
                Release-ComObject $pageSetup
                Release-ComObject $sheet
            }
        }
    }
    finally {
        Release-ComObject $worksheets
    }
}
catch {
    $primaryError = $_
}
finally {
    if ($null -ne $workbook) {
        try {
            [void](Invoke-ComMethod $workbook "Close" @($false))
        }
        catch {
            $cleanupError = $_
        }
        Release-ComObject $workbook
    }
    if ($null -ne $excel) {
        try {
            [void](Invoke-ComMethod $excel "Quit")
        }
        catch {
            if ($null -eq $cleanupError) {
                $cleanupError = $_
            }
        }
        Release-ComObject $excel
    }
    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()
    if ($excelProcessId -gt 0) {
        $ownedExcelProcess = Get-Process -Id $excelProcessId -ErrorAction SilentlyContinue
        if ($null -ne $ownedExcelProcess) {
            try {
                if (-not $ownedExcelProcess.WaitForExit(5000)) {
                    Stop-Process -Id $excelProcessId -Force -ErrorAction Stop
                    [void]$ownedExcelProcess.WaitForExit(5000)
                }
            }
            catch {
                if ($null -eq $cleanupError) {
                    $cleanupError = $_
                }
            }
            finally {
                $ownedExcelProcess.Dispose()
            }
        }
    }
}

if ($null -ne $primaryError) {
    throw $primaryError
}
if ($null -ne $cleanupError) {
    throw "Excel conversion completed, but Excel cleanup failed: $($cleanupError.Exception.Message)"
}
