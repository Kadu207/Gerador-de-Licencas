# 13 - Finalizador e exportacao de documentos

## # Objetivo
Gerar artefatos finais de projeto a partir de um unico Markdown:
- `.docx`
- `.pptx`
- `.pdf` (opcional)

## # Dependencias
- Python 3.10+
- Instalar:
  - `pip install -r scripts/finalizador_requirements.txt`

## # Uso
- Gerar relatorio consolidado em Markdown (ex.: `relatorio_projeto.md`).
- Executar:
  - `python scripts/finalizador_converter.py relatorio_projeto.md`

## # Saida
Na mesma pasta do arquivo de entrada:
- `relatorio_projeto.docx`
- `relatorio_projeto.pptx`
- `relatorio_projeto.pdf` (se `weasyprint` estiver instalado e funcional)

## # Observacoes para Windows
- Se o PDF falhar por bibliotecas nativas, use WSL2 ou mantenha DOCX/PPTX como saida principal.
