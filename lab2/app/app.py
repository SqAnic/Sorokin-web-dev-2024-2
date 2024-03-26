from flask import Flask, render_template, request, make_response

app = Flask(__name__)
application = app

def num_checker(num):
    counter = 0
    symbols = [' ', '(', ')', '-', '+', '.']
    numbers = ['1', '2', '3', '4' , '5' , '6', '7', '8', '9', '0']
    new_num = ''
    for char in num:
        if char not in symbols and char not in numbers:
            error = 'Недопустимый ввод. В номере телефона встречаются недопустимые символы.'
            return error
        elif char in numbers:
            counter += 1
    if (num[0] == '8' and counter == 11) or (num[:2] == '+7' and counter == 11):
        return 1
    elif (num[0] != '8' and num[:2] != '+7') and counter == 10:
        return 2
    else:
        error = 'Недопустимый ввод. Неверное количество цифр.'
        return error

def num_transform(num, flag):    
    new_num = ''
    for i in range(len(num)):
        try:
            int(num[i])
        except ValueError:
            continue
        if len(new_num) == 0 and flag == 1:
            new_num += '8'
            continue
        if flag == 2 and len(new_num) == 0:
            new_num += '8'
        new_num += num[i]
    formatted_number = "8-{}-{}-{}-{}".format(new_num[1:4], new_num[4:7], new_num[7:9], new_num[9:])
    return formatted_number

    
@app.route('/')
def index():
    url = request.url
    return render_template('index.html', url=url)

@app.route('/args')
def args():
    return render_template('args.html')

@app.route('/headers')
def headers():
    return render_template('headers.html')

@app.route('/cookies')
def cookies():
    response = make_response(render_template('cookies.html'))
    if "User"  not in request.cookies:
        response.set_cookie("User","Hello World!")
    else:
        response.delete_cookie("User")
    return response

@app.route("/form", methods = ["POST", "GET"])
def form():
    return render_template("forms.html")

@app.route('/number', methods = ["POST", "GET"])
def number():
    text = ''
    error = ''
    input_class = ''
    if request.method == "POST":
        ph_number = request.form.get('ph_number')
        result = num_checker(ph_number)
        if isinstance(result, str): 
            error = result
            input_class = 'is-invalid'
        elif result in [1, 2]:
            text = num_transform(ph_number, result)
            input_class = 'is-valid'
        
    return render_template("number.html", text=text, error=error, input_class=input_class)

@app.route("/calc", methods = ["POST", "GET"])
def calc():
    res = 0
    error = ''
    if request.method == "POST":
        try:
            a = float(request.form['a'])
            op = request.form['operation']
            b = float(request.form['b'])
            match op:
                case '+':
                    res = a + b
                case '-':
                    res = a - b
                case '/':
                    res = a / b
                case '*':
                    res = a * b
        except ZeroDivisionError:
            error = 'Деление на 0 невозможно'
        except ValueError: 
            error = 'Неверный тип данных'
        
    return render_template("calc.html", res = res, error = error)
