stty -F $1 300

python -c 'print("/?!\x0d\x0a", end="", flush=True)' | cat $1

sleep .5

#stty -F $1 9600

python -c 'print("\x06050\x0d\x0a", end="", flush=True)' | cat $1
