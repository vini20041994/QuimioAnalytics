# S2 Dia 5 - Pacote Unico de Validacao com Especialista

---

## Identificacao

| Campo | Valor |
|---|---|
| Data | 2026-05-20 |
| Projeto | QuimioAnalytics |
| Sprint | Sprint 2 - Paradigma de Ranking |
| Referencia interna | S2-07 - Validacao da ordenacao biologica |

---

## Leitura rapida (1 minuto)

Voce recebera apenas 2 arquivos:
- Este documento (guia de preenchimento).
- Uma planilha Excel com os grupos para revisao.

Sua tarefa e simples:
1. Ler cada grupo no Excel na ordem em que os candidatos aparecem.
2. Marcar uma decisao por grupo.
3. Preencher o parecer final ao fim da revisao.

Tempo estimado:
- Revisao rapida (amostra parcial): 30 a 45 minutos.
- Revisao completa (100 grupos): 1h30 a 2h.

---

## 1) Objetivo da avaliacao

Pergunta principal:

**A ordem dos candidatos apresentada pelo sistema faz sentido biologico para apoio a decisao humana?**

Importante:
- Nao e necessario conhecimento em dados, programacao ou banco de dados.
- A avaliacao deve focar somente na coerencia biologica da ordem apresentada.

---

## 2) Escopo e materiais de revisao

Escopo tecnico desta rodada:
- Dataset de origem: data/staging/biological_ranking_candidates.parquet
- Amostra selecionada: 100 feature_group
- Estratificacao: 50 com empate e 50 sem empate
- Total de linhas para revisao: 1531

Arquivos para revisao:
- data/staging/s2_dia5_amostra_100_features.xlsx
- data/staging/s2_dia5_amostra_100_features.csv

Campos incluidos na revisao:
- feature_group
- original_id
- fragment_score
- isotope_similarity
- mass_error_ppm
- formula
- rank_group
- is_tied

---

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

---

## 4) Regras de decisao

Marque **aprovado** quando:
- A prioridade dos candidatos parece coerente com o raciocinio biologico esperado.
- Empates aparentam corretos quando ha candidatos equivalentes.

Marque **ajuste necessario** quando:
- Existe inversao clara de prioridade biologica.
- Empate foi mantido quando nao deveria, ou nao foi mantido quando deveria.

Marque **inconclusivo** quando:
- Faltam elementos para concluir com seguranca.

---

## 5) Roteiro sugerido da sessao

1. Revisar 20 casos com rank_group = 1 (prioridade biologica).
2. Revisar 20 casos com empate (is_tied = true).
3. Revisar 20 casos sem empate para contraste.
4. Revisar 40 casos aleatorios adicionais para cobertura.
5. Registrar decisao por feature_group: aprovado, ajuste necessario ou inconclusivo.

## 2) O que voce precisa abrir

Arquivo principal de revisao:
- Planilha Excel da amostra de 100 grupos (enviada junto com este documento).

Este documento serve para:
- Entender as regras de decisao.
- Registrar o parecer final.
- Padronizar o retorno.

---

## 3) Passo a passo simplificado (por grupo)

Para cada feature_group no Excel:

1. Olhe os candidatos de cima para baixo (essa e a ordem proposta).
2. Pergunte: "Os primeiros colocados fazem sentido biologico?"
3. Se houver empate (is_tied = true), pergunte: "Esse empate e aceitavel biologicamente?"
4. Registre uma decisao:
	- aprovado
	- ajuste necessario
	- inconclusivo
5. Se marcar "ajuste necessario" ou "inconclusivo", escreva 1 observacao curta.

Atalho de decisao:
- Se esta biologicamente coerente: aprovado.
- Se ha inversao clara de prioridade: ajuste necessario.
- Se faltam elementos para concluir: inconclusivo.

---

## 4) Regras de decisao (objetivas)

Marque **aprovado** quando:
- A ordem geral parece coerente biologicamente.
- Empates parecem adequados para candidatos equivalentes.

Marque **ajuste necessario** quando:
- Um candidato claramente mais plausivel ficou abaixo de outro menos plausivel.
- O empate deveria existir e nao existe, ou foi mantido sem justificativa.

Marque **inconclusivo** quando:
- Nao ha informacao suficiente para tomar decisao segura.

---

## 5) Exemplo pratico (como preencher)

Exemplo de registro por grupo:
- feature_group: FG_023
- decisao: ajuste necessario
- observacao curta: candidato B deveria estar acima de A por maior coerencia biologica.

Regra de ouro:
- Use observacoes curtas e diretas (1 linha).

---

## 6) Criterio de aceite da validacao

A validacao sera considerada aprovada quando:
- Pelo menos 90% dos grupos forem marcados como aprovado.
- Nao houver indicio de erro sistemico na ordenacao.

---

## 7) Registro rapido durante a revisao

Sugestao:
1. Revise em blocos de 20 grupos.
2. A cada bloco, salve a planilha.
3. Ao final, transfira o resultado global para o formulario abaixo.

---

## 8) Status desta execucao

| Item | Status |
|---|---|
| Preparacao de evidencias | CONCLUIDA |
| Amostra e planilha de revisao | CONCLUIDAS |
| Sessao com especialista | PENDENTE |
| Assinatura do parecer final | PENDENTE |

---

## 9) Formulario de parecer final

Especialista responsavel: ____________________________________________

Instituicao/area: _________________________________________________

Data da avaliacao: ____ / ____ / ______

Resultado global:
- [ ] aprovado
- [ ] aprovado com observacoes
- [ ] reprovado

Texto de parecer (copiar e completar):

"A ordem dos candidatos apresentada pelo sistema faz sentido biologico para apoio a decisao humana, considerando os casos revisados nesta amostra."

Assinatura: _______________________________________________________

---

## 10) Quadro para registro das observacoes

| feature_group | decisao | observacao curta |
|---|---|---|
| exemplo_1 | aprovado | ordem coerente |
| exemplo_2 | ajuste necessario | candidato X deveria estar acima de Y |
| exemplo_3 | inconclusivo | faltam evidencias complementares |

---

## 11) Texto de email pronto para envio

Assunto:

Validacao tecnica da ordenacao biologica - amostra de 100 features (QuimioAnalytics)

Corpo do email:

Prezados(as),

Estamos realizando a validacao tecnica da ordenacao biologica de candidatos.

Voce recebera apenas:
- 1 planilha Excel com os grupos para revisao.
- 1 documento com o passo a passo e o formulario de parecer.

Objetivo da revisao:
Validar se a ordem dos candidatos faz sentido biologico para apoio a decisao humana.

Como registrar o retorno:
- Para cada feature_group, marcar: aprovado, ajuste necessario ou inconclusivo.
- Ao final, preencher o parecer global e assinatura no documento.

Prazo sugerido de retorno:
- [preencher]

Contato para suporte durante a revisao:
- [preencher nome e contato]

Agradecemos o apoio nesta etapa critica para a qualidade cientifica do projeto.

---

## 12) Contato para suporte durante a avaliacao

- Contato tecnico do projeto: [preencher]
- Prazo sugerido para retorno: [preencher]

---

## 13) Observacoes finais

- Este documento foi simplificado para uso externo com Excel + guia, sem necessidade de acesso ao projeto.
- O aceite S2-07 sera marcado como concluido apos parecer assinado do especialista.
