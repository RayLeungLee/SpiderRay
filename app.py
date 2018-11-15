from flask import Flask, request
import requests, json, os

app = Flask(__name__)

app.scrapyd_url = ''


@app.route('/gxyf/clients', methods=['GET'])
def clients():
    try:
        with open('./conf/conf.json', "r", encoding="utf-8") as f:
            conf_json = json.load(f)
            data_json = {'status':'ok', 'data': []}
            data_json['data'] = conf_json
            return json.dumps(data_json)
    except Exception as e:
        print(e)
        data_json = {'status': 'error', 'msg': '暂未找到服务器'}
        return json.dumps(data_json)


@app.route('/gxyf/updateConf', methods=['GET'])
def updateConf():
    try:
        name = request.args.get('name')
        type = request.args.get('type')
        with open('./conf/conf.json', "r", encoding="utf-8") as f:
            conf_json = json.load(f)
            if type == 'add':
                host = request.args.get('host')
                port = request.args.get('port')
                conf_json_obj = {
                    'title': host + ':' + port,
                    'host': host,
                    'port': port,
                    'name': name
                }
                conf_json.append(conf_json_obj)
            elif type == 'remove':
                conf_json_new = []
                for c in conf_json:
                    if c['name'] != name:
                        conf_json_obj = {
                            'title': c['title'],
                            'host': c['host'],
                            'port': c['port'],
                            'name': c['name']
                        }
                        conf_json_new.append(conf_json_obj)
                conf_json = conf_json_new
    except Exception as e:
        print(e)
        data_json = {'status': 'error', 'msg': '暂未找到服务器'}
        return json.dumps(data_json)
    with open('./conf/conf.json', "w", encoding="utf-8") as f:
        json.dump(conf_json, f, ensure_ascii=False)
    data_json = {'status':'ok'}
    return json.dumps(data_json)

@app.route('/gxyf/daemonstatus', methods=['GET'])
def daemonstatus():
    host = request.args.get('host')
    port = request.args.get('port')
    app.scrapyd_url = "http://"+host+":"+port
    url = app.scrapyd_url + "/daemonstatus.json"
    try:
        resp = requests.get(url)
    except Exception as e:
        print(e)
        data_json = {'status': 'error', 'msg': '连接不上该服务器，正在尝试重新连接，请检查地址是否有误或服务是否开启'}
        return json.dumps(data_json)
    data_json = json.loads(resp.text)
    return json.dumps(data_json)

@app.route('/gxyf/start', methods=['GET'])
def start():
    project = request.args.get('project')
    spider = request.args.get('spider')
    url = app.scrapyd_url + "/schedule.json"
    params = {"project": project, "spider": spider}
    try:
        resp = requests.post(url, data=params)
    except Exception as e:
        print(e)
        data_json = {'status': 'error', 'msg': '服务器连接异常'}
        return json.dumps(data_json)
    data_json = json.loads(resp.text)
    return json.dumps(data_json)

@app.route('/gxyf/stop', methods=['GET'])
def stop():
    project = request.args.get('project')
    job = request.args.get('job')
    url = app.scrapyd_url + "/cancel.json"
    params = {"project": project, "job": job}
    try:
        resp = requests.post(url, data=params)
    except Exception as e:
        print(e)
        data_json = {'status': 'error', 'msg': '服务器连接异常'}
        return json.dumps(data_json)
    data_json = json.loads(resp.text)
    return json.dumps(data_json)


@app.route('/gxyf/delete', methods=['GET'])
def delete():
    project = request.args.get('project')
    url = app.scrapyd_url + "/delproject.json"
    params = {"project": project}
    try:
        resp = requests.post(url, data=params)
    except Exception as e:
        print(e)
        data_json = {'status': 'error', 'msg': '服务器连接异常'}
        return json.dumps(data_json)
    data_json = json.loads(resp.text)
    return json.dumps(data_json)


@app.route('/gxyf/status', methods=['GET'])
def status():
    projects = request.args.get('project')
    data_array = []
    if projects == '':
        noPro = {
            'msg': '该服务器暂无爬取记录',
            'status': 'error'
        }
        data_array.append(noPro)
        return json.dumps(data_array)
    projects = projects.split(',')
    for project in projects:
        url = app.scrapyd_url + "/listjobs.json?project="+project
        try:
            resp = requests.get(url)
        except Exception as e:
            print(e)
            data_json = {'status': 'error', 'msg': '服务器连接异常'}
            return json.dumps(data_json)
        data_json = json.loads(resp.text)
        data_json = can_status_dict(data_json, project)
        data_array.append(data_json)
    print(data_array)
    return json.dumps(data_array)


@app.route('/gxyf/upload', methods=['POST'])
def upload():
    files = request.files['file']
    project = request.form['project']
    version = request.form['version']
    if files:
        new_fname = r'eggs/' + project + '.egg'
        files.save(new_fname)

    files = {'egg': (open('eggs/'+project+'.egg', 'rb'))}
    url = app.scrapyd_url + "/addversion.json"
    params = {"project": project, "version": version}
    try:
        resp = requests.post(url, data=params, files=files)
    except Exception as e:
        print(e)
        data_json = {'status': 'error', 'msg': '服务器连接异常'}
        return json.dumps(data_json)
    data_json = json.loads(resp.text)
    os.remove('eggs/'+project+'.egg')
    return json.dumps(data_json)


@app.route('/gxyf/can_data_list', methods=['GET'])
def can_data_list():
    # 初始化 data_dict
    data_dict = {'status': 'ok','data':[]}
    # 列出 scrapyd 部署过的项目
    pro_list_url = app.scrapyd_url + "/listprojects.json"
    try:
        pro_data = requests.get(pro_list_url)
    except Exception as e:
        print(e)
        data_json = {'status': 'error', 'msg': '服务器连接异常'}
        return json.dumps(data_json)
    pro_list = can_data_dict(pro_data, 'projects')

    if len(pro_list) == 0:
        noProObj = {
            'msg': '该服务器暂无爬虫项目',
            'status': 'error'
        }
        return json.dumps(noProObj)
    else:
        # 列出项目下的所有爬虫
        for pro_name in pro_list:
            pro_obj = []
            spi_list_url = app.scrapyd_url + "/listspiders.json?project=" + pro_name
            try:
                spi_data = requests.get(spi_list_url)
            except Exception as e:
                print(e)
                data_json = {'status': 'error', 'msg': '服务器连接异常'}
                return json.dumps(data_json)
            spi_list = can_data_dict(spi_data, 'spiders')
            if len(spi_list) != 0:
                for spi_name in spi_list:
                    pro_spi = {}
                    pro_spi['pro_name'] = pro_name
                    pro_spi['spi_name'] = spi_name
                    pro_obj.append(pro_spi)
            data_dict['data'].append(pro_obj)
        print('项目与爬虫列表:', data_dict)
    return json.dumps(data_dict)


# 数据处理 json数据拿出指定的list
def can_data_dict(data, name):
    data_json = json.loads(data.text)
    if data_json['status'] == 'ok':
        list = data_json[name]
        return list
    else:
        return 'error'

# job　数据处理
def can_status_dict(data_json, project):
    status = ['pending', 'running', 'finished']
    for st in status:
        i=0
        while i < len(data_json[st]):
            data_json[st][i]['project'] = project
            if st == 'running' or st == 'finished':
                data_json[st][i]['start_time'] = data_json[st][i]['start_time'][0:19]
                data_json[st][i]['log'] = app.scrapyd_url + '/logs/' + data_json[st][i]['project'] + '/' + data_json[st][i]['spider'] + '/' + data_json[st][i]['id'] + '.log'
            if st == 'finished':
                data_json[st][i]['end_time'] = data_json[st][i]['end_time'][0:19]
            i += 1
    return data_json

if __name__ == '__main__':
    # app.run(debug=True)
    app.run(host='0.0.0.0', port=5001)
