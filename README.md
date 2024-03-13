# Telegram Task Reminder Bot

Este é um bot Telegram desenvolvido em Python que ajuda os usuários a gerenciar suas tarefas diárias, fornecendo lembretes e funcionalidades de adição, edição e remoção de tarefas.

## Funcionalidades
- Adicionar tarefas fixas e extras.
- Editar tarefas existentes.
- Remover tarefas.
- Listar tarefas agendadas.
- Receber lembretes das próximas tarefas.
- Mensagem matinal para listar as tarefas do dia.

## Pré-requisitos
- Python 3.x instalado.
- Conta no Telegram
- Token da API do Telegram
- Chat ID da conversa

## Instalação
1. Clone este repositório:
   
   ```
   git clone https://github.com/gsilva1602/bot_telegram
2. Instale as dependências necessárias:
   
   ```
   pip install -r requirements.txt
3. Obtenha um Token API seguindo as instruções em [BotFather](https://core.telegram.org/bots#botfather).
4. Substitua o valor "YOUR_KEY" no arquivo bottelegram.py pelo seu token.
5. Obtenha o Chat ID em acessando "https://api.telegram.org/bot{bot_token}/getUpdates".
6. Substitua o valor "YOUR_CHAT" no arquivo bottelegram.py pelo seu Id.
7. Execute o bot:
   ```
   python bottelegram.py
## Uso
- Use 'task', o bot fornecerá uma lista de opções para interação.
- Use 'adicionar' para adicionar uma nova tarefa, escolhendo entre tarefas fixas ou extras.
- Use 'editar' para editar uma tarefa existente, selecionando o tipo de tarefa (fixa ou extra) e o horário da tarefa a ser editada.
- Use 'remover' para remover uma tarefa existente, escolhendo o tipo de tarefa (fixa ou extra) e o horário da tarefa a ser removida.
- Use 'lembrar' para receber um lembrete da próxima tarefa agendada.
- Use 'listar' para ver a lista de tarefas programadas.

## Contribuição
Contribuições são sempre bem-vindas!
Se você encontrar algum problema ou tiver sugestões para melhorar o bot,
sinta-se à vontade para abrir uma issue ou enviar um pull request.

## Autores
- Gustavo Silva Almeida (@gsilva1602)

## Licença
Este projeto está licenciado sob a [Licença MIT](https://github.com/seu-usuario/nome-do-repositorio/blob/main/LICENSE).
