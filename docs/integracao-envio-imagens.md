# Integração de upload de imagens — Impulse

## Objetivo
Transferir a arte final aprovada para o repositório, sem redesenhar a logo nem degradar a imagem. O GitHub hospeda a imagem pública; o Supermetrics publica sua URL após verificação.

## Componentes implementados
- `scripts/import_asset.py`: importa mídias de URL HTTPS pública via GitHub Actions; importação já testada em execução real.
- `scripts/upload_from_file.py`: envia arquivo local pela API Contents do GitHub, convertendo os bytes em Base64 internamente.
- `tests/test_upload_from_file.py`: valida formato, caminhos, proteção contra sobrescrita e transmissão de Base64.
- `.github/workflows/qa-media-upload.yml`: executa os testes automaticamente no GitHub Actions.

## Uso em ambiente com acesso à imagem e rede
Exige `GITHUB_TOKEN` configurado como segredo, com permissão fine-grained Contents: Read and write somente neste repositório. Nunca incluir tokens em commits.

```bash
export GITHUB_TOKEN="<TOKEN_GUARDADO_NO_SECRET_MANAGER>"
python3 scripts/upload_from_file.py /caminho/arte-aprovada.jpg posts/2026/11/arte-aprovada.jpg
```

O script recusa substituir arquivo existente e devolve URL pública, commit e hash SHA-256. Não publica nas redes sozinho.

## Situação da integração com este chat
O envio por API está implementado e passou nos testes unitários com API simulada. Entretanto, o conector do GitHub neste chat não recebe anexos binários e o ambiente que contém os arquivos locais não tem saída de rede. Ainda não existe uma ponte para transferir diretamente esses bytes ao GitHub.

Para completar a automação será necessário um conector que aceite anexos do ChatGPT e execute o uploader com credenciais mantidas em ambiente seguro; ou uma URL HTTPS da imagem ORIGINAL, consumida pelo importador atual. Miniaturas não servem.

## Critérios para declarar o fluxo automático
1. Receber a imagem final gerada no chat sem upload manual.
2. Confirmar novo arquivo em `posts/YYYY/MM/` no GitHub.
3. Verificar o SHA-256 e as dimensões.
4. Passar URL HTTPS original ao Supermetrics, validar e publicar somente com autorização.
5. Recuperar os links de Instagram e LinkedIn, confirmando o resultado.

Agendamento confirmado não equivale a publicação efetiva.
