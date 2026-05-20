# Validacao da Ordenacao Biologica - Documento para Especialistas

Data: 2026-05-20
Projeto: QuimioAnalytics
Referencia interna: Sprint 2 - Paradigma de Ranking

## 1) Objetivo desta avaliacao

Este documento pede uma validacao de criterio tecnico-cientifico.

Pergunta principal:
A ordem dos candidatos apresentada pelo sistema faz sentido biologico para apoio a decisao humana?

Importante:
- Nao e necessario conhecimento em dados, programacao ou banco de dados.
- A avaliacao deve focar somente na coerencia biologica da ordem apresentada.

## 2) O que voces vao receber

- Um arquivo com 100 grupos de features para revisao.
- Em cada grupo, os candidatos ja aparecem ordenados.
- Alguns grupos tem empate explicito, para validar se o empate e biologicamente aceitavel.

Arquivo de revisao:
- data/staging/s2_dia5_amostra_100_features.xlsx
- data/staging/s2_dia5_amostra_100_features.csv (versao alternativa)

## 3) Como avaliar (passo a passo)

Para cada feature_group:

1. Leia os candidatos na ordem em que aparecem.
2. Verifique se os primeiros colocados fazem sentido biologico.
3. Nos casos com empate (is_tied = true), confirme se manter mais de uma opcao e adequado.
4. Marque uma das decisoes abaixo.

Decisoes possiveis:
- aprovado: a ordem faz sentido biologico
- ajuste necessario: ha um problema claro na ordem
- inconclusivo: nao ha informacao suficiente para decidir

## 4) Regras de decisao simples

Marque aprovado quando:
- A prioridade dos candidatos parece coerente com o raciocinio biologico esperado.
- Empates aparentam corretos quando ha candidatos equivalentes.

Marque ajuste necessario quando:
- Existe inversao clara de prioridade biologica.
- Empate foi mantido quando nao deveria, ou nao foi mantido quando deveria.

Marque inconclusivo quando:
- Faltam elementos para concluir com seguranca.

## 5) Criterio de aceite da validacao

A validacao sera considerada aprovada quando:
- Pelo menos 90% dos grupos forem marcados como aprovado.
- Nao houver indicio de erro sistemico na ordenacao.

## 6) Formulario de parecer final

Especialista responsavel:
Instituicao/area:
Data da avaliacao:

Resultado global:
- aprovado
- aprovado com observacoes
- reprovado

Texto de parecer (copiar e completar):
"A ordem dos candidatos apresentada pelo sistema faz sentido biologico para apoio a decisao humana, considerando os casos revisados nesta amostra."

Assinatura:

## 7) Quadro para registro das observacoes

Use este formato para registrar os pontos principais encontrados.

| feature_group | decisao | observacao curta |
|---|---|---|
| exemplo_1 | aprovado | ordem coerente |
| exemplo_2 | ajuste necessario | candidato X deveria estar acima de Y |
| exemplo_3 | inconclusivo | faltam evidencias complementares |

## 8) Contato para suporte durante a avaliacao

Se houver duvida de preenchimento:
- Contato tecnico do projeto: [preencher]
- Prazo sugerido para retorno: [preencher]

Observacao final:
Este documento foi desenhado para avaliacao de dominio. Nenhuma etapa exige conhecimento de dados ou ferramentas tecnicas.
