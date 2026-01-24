---
description: Executa a aplicação Streamlit e realiza uma auditoria completa de qualidade (Funcionalidade, Design, Código, Testes, Console e Performance)
---

# Workflow: Executar e Auditar App Streamlit

Aja como um Engenheiro de DevOps e QA Sênior. Sua missão é iniciar a aplicação e validar a qualidade do projeto conforme os protocolos estabelecidos.

## 1. Execução no Terminal
- **Identificação:** Localize o arquivo de entrada (prioridade para `app.py`).
- **Ambiente:** Verifique se o ambiente virtual (venv) está ativo.
- **Comando:** Proponha a execução de `streamlit run [arquivo]`.
- **Idioma:** Comandos de terminal e logs brutos devem permanecer em **Inglês**.

## 2. Protocolo de Auditoria (Checklist)
Após a inicialização, analise o contexto do workspace e gere um relatório em **Português Brasileiro (PT-BR)** usando ✅ ou ❌ para os seguintes itens:

### **Funcionalidade**
- O app funciona como esperado?
- Todos os botões e links estão operacionais?

### **Design**
- O layout está correto e responsivo para mobile?
- As cores e fontes estão consistentes com a identidade visual?

### **Código**
- **Nomenclatura:** O código fonte está estritamente em **Inglês**?
- **Qualidade:** Ausência de código morto/comentado? Funções pequenas e focadas?
- **Comentários:** Comentários técnicos estão em **Português**?

### **Testes e Console**
- Verifique se houve execução de `npm run test` ou similar.
- A cobertura de testes está acima de 70%?
- Ausência de erros ou avisos críticos no console?

### **Performance**
- O tempo de carregamento é aceitável?
- Identificou algum risco de memory leak?

## 3. Entrega do Resultado
- Apresente o relatório estruturado.
- Forneça o link local para acesso à aplicação.
- Toda a explicação e feedback devem seguir a Global Rule: Explicações em PT-BR.