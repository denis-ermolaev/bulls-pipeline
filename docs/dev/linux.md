# Полезные команды
```bash
less -SN файл-для-чтения
```
`-S` - видно строки
`-N` - прокрутка влево-вправо
`+G` - чтение файла с конца
`+F` - следить за файлом в реальном времени(Ctrl+C - ручная навигация, F - возврат к слежению)
Позволяет читать .vcf.gz в терминале



### tmux

Команды управления внутри tmux:

`<C-b d>` - отключиться от сессии
`<C-b c>` - новое окно
`<C-b n>` - следующее окно
`<C-b p>` - предыдущее окно
`<C-b 0>` - переключиться на номер окна

```bash
# Список сессий
tmux ls

# Подключится к сессии
tmux attach -t session1

# Завершить сессию
tmux kill-session -t session1

# Завершить все сессии
tmux kill-server

```

# Настройки
## История
```bash
#.bashrc
# История
HISTSIZE=10000
HISTFILESIZE=20000
HISTCONTROL=ignoredups:erasedups
shopt -s histappend

# Синхронизация истории между окнами в реальном времени
PROMPT_COMMAND="history -a; history -n; $PROMPT_COMMAND"

# Поиск по истории через стрелочки (начни вводить команду и жми вверх)
bind '"\e[A": history-search-backward'
bind '"\e[B": history-search-forward'
```
