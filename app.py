from flask import Flask, render_template, request, jsonify
from flask_mysqldb import MySQL
import inspect,requests,pymysql,warnings
import db_config

app = Flask(__name__)
env='test'

mysql = MySQL(app)

@app.route('/',endpoint='index')
def index():
    return render_template('index.html',host=['local','uat','python_anywhere'])


@app.route('/execute_query', methods=['POST'])
def execute_query(): 
    try:
        warnings.simplefilter("ignore")
        if env=='proxy':
            try:
                cmd=proxy().convert_to_string(execute)
                cmd+=f"x=execute().run('{request.form['query']}')\n"
                cmd+="write(x)"
                result=proxy().proxy_run(cmd)
                result=result.get('Data',result)
                return result[0]
            except Exception as e:print(str(e))
        else:
            result=execute(db_config.db[request.form['host']]).run(request.form['query'])
        return jsonify(result)
    except Exception as e:print(str(e));return str(e)
    

#backend
class execute:
    def __init__(self,db): 

        self.host=db['host']
        self.user=db['user']
        self.password=db['password']
        self.db=db['db']
        self.port=db['port']
        
    def connect(self):
        try:
            self.connection=pymysql.connect(host=self.host,user=self.user,password=self.password,port=int(self.port),db=self.db,charset='utf8mb4')
            self.cursor=self.connection.cursor()
        except Exception as e: raise (e)
    def run(self,query):
        self.connect()
        try:
            qlist=query.lower().split(' ')
            first_word=qlist[0]
            
            if first_word in ['select']:
                table=qlist[qlist.index('from')+1]
                x=self.cursor.execute(query)
                results = self.cursor.fetchall()
                columns = [column[0] for column in self.cursor.description]
                self.cursor.execute(f"SHOW KEYS FROM {table} WHERE Key_name = 'PRIMARY';")
                primary_key_info = self.cursor.fetchone()
                primary_key = primary_key_info[4] if primary_key_info else None
    
                return {'results': results,'table':table,'columns':columns,'primary':primary_key}
            elif first_word in ['show','describe']:
                x=self.cursor.execute(query)
                results = self.cursor.fetchall()
                return {'results': results}
            elif first_word in ['create','drop','truncate']:
                x=self.cursor.execute(query)
                return {'results': x}
            elif first_word in ['insert','update','delete','alter']:
                x=self.cursor.execute(query)
                self.connection.commit()
                return {'results': x}
            else:return {'results': 'Invalid query'}

        except Exception as e:return {'result': str(e)}
        finally:self.cursor.close()


import json
@app.route('/run_python', methods=['POST'])
def run_python():
    try:
        def print(x):Print.append(json.dumps(x))
        def write(x):Data.append(x)
        Print=[]
        Data=[]
        exec(request.form['cmd'])
        return jsonify({'Print':Print,'Data':Data})
    except Exception as e:return jsonify({'result': str(e)})

class proxy:
    def __init__(self):
        env='x'
        if env=='UAT':
            self.proxy_url='https://stgppdashboard.chola.murugappa.com/event'
            self.proxy_header=''

        else:
            self.proxy_url='https://viswa.pythonanywhere.com/run_python'
            self.proxy_header=''



    def convert_to_string(self,function):
        source = inspect.getsource(function)
        function_string='\n'.join(source.splitlines())+'\n'
        return function_string
    def proxy_run(self,cmd):     
        response=requests.post(self.proxy_url,headers=self.proxy_header,json={'cmd':cmd})
        try:result=response.json()
        except Exception:print(response.text);return {}
        return result
    

if __name__ == '__main__':
    app.run(debug=True)

