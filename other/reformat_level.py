name = ''  # переводит уровень из старой системы в новую! не запускать
to = name
with open(name) as file:
    read = file.readlines()
    size = len(read[0].split())
with open(to, mode='w') as file:
    for i in range(size):
        a = read[i]
        res = []
        for j in a.split():
            if j == '0':
                res.append('b0')
            if j == '1':
                res.append('h0')
            if j == '2':
                res.append('h1')
            if j == '3':
                res.append('h2')
            if j == '5':
                res.append('s0')
        file.write(' '.join(res) + '\n')
    file.writelines(read[size:])
