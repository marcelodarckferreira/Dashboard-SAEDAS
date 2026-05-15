### 1. Criar o Ambiente Virtual

No terminal, dentro da pasta raiz do projeto (`SAEDAS`), execute:

```powershell
python -m venv .venv
```

*Isso criará uma pasta chamada `.venv` contendo uma cópia isolada do Python.*

### 2. Ativar o Ambiente

Para que o terminal utilize o Python do ambiente virtual, você precisa ativá-lo

```powershell
.\.venv\Scripts\activate
```

*Após executar, você verá `(.venv)` aparecer no início da linha do seu terminal.*

### 3. Instalar as Dependências

Com o ambiente ativado, instale as bibliotecas necessárias listadas no `requirements.txt`:

```powershell
pip install -r requirements.txt
```

### Comandos Úteis

* **Desativar:** Digite apenas `deactivate`.
* **Verificar se está ativo:** Execute `where python`. O caminho deve apontar para dentro da pasta `.venv`.
* **Limpar ambiente:** Se precisar resetar, basta deletar a pasta `.venv` e repetir o passo 1.

---

> [!TIP]
> Sempre que abrir um novo terminal para trabalhar no projeto, lembre-se de executar o comando de **ativação** (Passo 2) para garantir que o Streamlit e as outras bibliotecas funcionem corretamente.

### 1. Remover a pasta .venv (PowerShell)

```powershell
Remove-Item -Recurse -Force .venv
```

### 2. Criar o novo ambiente (Certifique-se de ter instalado o Python 3.12)

```powershell
exit
```

### 3. Ativar e instalar

```powershell
.\.venv\Scripts\activate
pip install -r requirements.txt
```
