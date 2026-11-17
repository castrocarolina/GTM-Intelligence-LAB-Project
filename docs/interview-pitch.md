# Interview pitch: GTM Intelligence Lab

## Portuguese (about 2 minutes)

Eu construí o GTM Intelligence Lab para responder a uma pergunta prática de growth: como transformar dados transacionais em decisões melhores de marketing e posicionamento por grupo de clientes?

O fluxo começa com pedidos e clientes do Olist. Quando os arquivos não estão disponíveis, o app gera um conjunto sintético reproduzível para que a demonstração continue funcionando. A partir dos pedidos, crio uma tabela por cliente com recência, frequência, receita e recompra. Depois uso essas variáveis de RFM em um K-means. Não escolhi o número de grupos no chute: comparo inertia pelo método elbow e silhouette, e mostro esses diagnósticos na interface.

Em seguida, estimo o LTV com uma fórmula simples baseada em frequência, ticket médio, recência e uma margem bruta assumida. Preferi começar por algo explicável em vez de apresentar um modelo probabilístico sem conseguir defender suas hipóteses. O resultado é uma estimativa direcional, não uma previsão financeira validada.

Na parte de product marketing, o usuário pode gerar um brief por segmento com persona, dor, proposta de valor, mensagens, canal e hipóteses de teste A/B. A integração com Anthropic é opcional; sem chave de API, o app continua demonstrável com um brief local.

Também criei um simulador de realocação de orçamento entre canais. Como o Olist não contém gastos de mídia, os investimentos por canal são simulados e claramente identificados. O simulador transfere o mesmo valor entre canais e mostra um impacto estimado com premissas explícitas; não afirmo que seja causal.

O principal aprendizado foi conectar analytics à decisão: não basta criar segmentos, é preciso mostrar o que cada grupo pode significar para retenção, aquisição e mensagem. Se eu continuasse o projeto, validaria os segmentos com dados reais de mídia, margem e campanhas e compararia as recomendações com resultados de experimentos.

## English (about 2 minutes)

I built the GTM Intelligence Lab to answer a practical growth question: how can transaction data lead to better marketing and positioning decisions for different customer groups?

The workflow starts with Olist customer and order data. If those files are unavailable, the app creates a reproducible synthetic sample so the demo remains usable. I aggregate orders into a customer-level table with recency, frequency, revenue, and repeat-purchase behavior. Then I apply K-means to the RFM features. The number of clusters is not chosen arbitrarily: I compare elbow inertia and silhouette scores, and expose those diagnostics in the app.

Next, I estimate customer and segment LTV using a simple formula based on purchase frequency, average order value, recency, and an assumed gross margin. I chose an explainable baseline rather than presenting a probabilistic model whose assumptions I could not defend. The result is a directional estimate, not a validated financial forecast.

For product marketing, users can generate a brief for each segment, including a persona, key pain, value proposition, message variations, a recommended channel, objections, and A/B test hypotheses. Anthropic is optional; the local fallback keeps the product demoable without an API key.

I also built a budget reallocation simulator. Olist does not include media spend, so channel budgets are simulated and clearly labeled. The simulator transfers the same amount between two channels and estimates an impact using visible assumptions; it is not a causal model.

The main lesson was to connect analytics to action: segmentation is only useful when it helps frame retention, acquisition, and messaging decisions. My next step would be to validate the segments with real media, margin, and campaign data, then compare the recommendations with experiment results.

## Follow-up questions to prepare for

- **Why K-means?** It is a transparent baseline for scaled RFM features and easy to explain to business stakeholders.
- **Why this LTV approach?** It is an explainable starting point. I state its assumptions and avoid presenting it as calibrated predictive truth.
- **What is simulated?** Channel spend and channel-efficiency/segment-affinity assumptions. Olist transactions are separate from those simulated planning inputs.
- **How would you validate the recommendations?** Run controlled tests by segment and channel, compare incremental outcomes, and update the assumptions from observed results.
