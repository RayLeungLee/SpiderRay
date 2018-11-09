from flask import Flask, request
import requests, json, os

app = Flask(__name__)

@app.route('/gxyf/start', methods=['GET'])
def start():
    project = request.args.get('project')
    spider = request.args.get('spider')
    url = "http://localhost:6800/schedule.json"
    params = {"project": project, "spider": spider}
    resp = requests.post(url, data=params)
    data_json = json.loads(resp.text)
    return json.dumps(data_json)

@app.route('/gxyf/stop', methods=['GET'])
def stop():
    project = request.args.get('project')
    job = request.args.get('job')
    url = "http://localhost:6800/cancel.json"
    params = {"project": project, "job": job}
    resp = requests.post(url, data=params)
    data_json = json.loads(resp.text)
    return json.dumps(data_json)


@app.route('/gxyf/delete', methods=['GET'])
def delete():
    project = request.args.get('project')
    url = "http://localhost:6800/delproject.json"
    params = {"project": project}
    resp = requests.post(url, data=params)
    data_json = json.loads(resp.text)
    return json.dumps(data_json)


@app.route('/gxyf/status', methods=['GET'])
def status():
    projects = request.args.get('project')
    projects = projects.split(',')
    data_array = []
    for project in projects:
        url = "http://localhost:6800/listjobs.json?project="+project
        resp = requests.get(url)
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
    url = "http://localhost:6800/addversion.json"
    params = {"project": project, "version": version}
    resp = requests.post(url, data=params, files=files)
    data_json = json.loads(resp.text)
    os.remove('eggs/'+project+'.egg')
    return json.dumps(data_json)


@app.route('/gxyf/can_data_list', methods=['GET'])
def can_data_list():
    # 初始化 data_dict
    data_dict = {'status': 'ok','data':[]}
    # 列出 scrapyd 部署过的项目
    pro_list_url = "http://localhost:6800/listprojects.json"
    pro_data = requests.get(pro_list_url)
    pro_list = can_data_dict(pro_data, 'projects')

    if pro_list == 'error':
        return pro_list
    else:
        # 列出项目下的所有爬虫
        for pro_name in pro_list:
            pro_obj = []
            spi_list_url = "http://localhost:6800/listspiders.json?project=" + pro_name
            spi_data = requests.get(spi_list_url)
            spi_list = can_data_dict(spi_data, 'spiders')
            if spi_list == 'error':
                return spi_list
            else:
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
                data_json[st][i]['log'] = 'http://localhost:6800/logs/' + data_json[st][i]['project'] + '/' + data_json[st][i]['spider'] + '/' + data_json[st][i]['id'] + '.log'
            if st == 'finished':
                data_json[st][i]['end_time'] = data_json[st][i]['end_time'][0:19]
            i += 1
    return data_json

if __name__ == '__main__':
    app.run()
    # app.run(debug=True,host='0.0.0.0', port=8080)
