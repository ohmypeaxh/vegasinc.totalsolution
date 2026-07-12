# Phase 2 DQ Domain Foundation

Phase 2 adds domain and service contracts only. It intentionally does not implement UI workflows, Naver CLOVA HTTP calls, OCR algorithms, URS parsing/classification/mapping algorithms, Word generation, or unrelated generators.

## Boundaries

- `models.ocr`: provider-neutral OCR configuration, request, page result, error, and aggregate result models.
- `services.ocr`: `OCRProvider` and `OCRService` abstractions plus page-isolating orchestration for fake/test providers and future real providers.
- `models.extraction`: document kind, extraction method, extraction policy, and page-level metadata with original/normalized/reviewed text and traceability.
- `services.extraction`: document text extractor boundary and policy evaluator. The contract prefers embedded text before OCR.
- `models.urs`: validated URS requirement model preserving original text separately from normalized text and review metadata.
- `services.urs_analysis`: parser/classifier/customer-strategy boundaries only.
- `models.dq_mapping`: DQ mapping relationship models for one-to-one, one-to-many, many-to-one, excluded, not-applicable, user response, and unmapped cases.
- `models.project` and `services.project_persistence`: versioned JSON project aggregate with UTF-8 atomic save, overwrite protection, supported-version validation, and secret-field rejection.

## Future phases

- Add provider adapters at secure configuration boundaries.
- Add concrete PDF/image extraction implementations.
- Add customer-specific URS parsing and classification strategies.
- Add DQ mapping/review workflows.
- Add Word/template generation after validated requirements and mappings are reviewed.
