# Importação automática de imagens

Este repositório já possui um workflow em `.github/workflows/import-approved-asset.yml` que baixa imagens de URLs HTTPS públicas e salva os arquivos em `posts/`, `videos/` ou `brand/logos/`.

## Caminho automatizado quando existir URL pública

O assistente pode criar em `requests/` um arquivo JSON como:

```json
{
  "asset_url": "https://media.canva.com/EXEMPLO/imagem.png",
  "target_path": "posts/2026/11/2026-11-10-regras-negocio.png"
}
```

O commit dispara o GitHub Actions, que verifica o arquivo (HTTPS, domínio, formato, tamanho e integridade opcional), salva a mídia e remove o pedido. O assistente deve **consultar o resultado da execução** e a presença do arquivo antes de declarar êxito.

A URL usada nos pedidos públicos **não pode conter tokens de acesso ou parâmetros de assinatura**, pois o JSON faz parte do histórico público do Git. O workflow aceita atualmente origens `media.canva.com`, `storage.googleapis.com`, `images.unsplash.com` e `res.cloudinary.com`.

Para URLs temporárias ou com query string, utilize a execução manual do workflow com entradas (workflow_dispatch), sem registrá-las em arquivos versionados. Ainda assim, não use URLs que exponham credenciais privadas.

## Limitação atual

O processo GitHub está pronto, mas a ferramenta que gera imagens no ChatGPT precisa disponibilizar a mídia em uma **URL HTTPS pública na resolução original**. Um link `sandbox:/mnt/data/` não é endereço público e o GitHub Actions não consegue utilizá-lo.

Até que essa origem esteja integrada, o fluxo **não é completamente autônomo**. Não considerar as mídias enviadas sem confirmar o commit com o arquivo binário.

## Identidade visual

Somente imagens revisadas e aprovadas podem ser transferidas. É obrigatório utilizar a marca oficial original, conforme a skill `impulse-social-media`. O ícone SVG não substitui a assinatura completa.
