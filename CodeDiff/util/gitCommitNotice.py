# -*- coding: UTF-8 -*-
__Author__ = "Sky Huang"

from datetime import datetime, timedelta
import git
import os
import pysvn
import re
import time
import json
import requests

tmp_path = 'E:\\jenkins_test'
# print(os.listdir(tmp_path))
# print(os.remove(os.path.join(tmp_path,os.listdir(tmp_path)[0])))
def deleteDir(tmp_path):
    # if os.listdir(tmp_path):
    #     os.remove(tmp_path)
    pass


# 获取git仓库代码commit情况
def getCommitMessagesByGit(repos, day_count):
    """
    :param repos: {"url":"svn://39.108.134.246/hlb/test/HttpRunnerManager-master"}
    :param day_count: 天数
    :return:
    """
    repos_list = repos.split(";")
    summary = []
    # 遍历列表中所有仓库
    for repo_str in repos_list:
        # 执行前清空临时文件夹
        # deleteDir(tmp_path)
        repo = json.loads(repo_str)
        project_name = repo['url'].split('/')[-1]
        project_title = project_name + '-' + repo['branch']
        repo['title'] = project_title
        work_dir = os.path.join(tmp_path, project_title)
        if 'http' not in repo['url']:
            repo['error'] = '仓库链接仅支持http/https的格式，请修改仓库链接。当前的仓库链接为：{}'.format(repo['url'])
            summary.append(repo)
            continue
        try:
            # 克隆到本地
            # git.Repo.clone_from(repo['url'], work_dir, branch=repo['branch'], progress=None)
            repository = git.Repo(work_dir)
            print("克隆完毕！！！！")
            results = []
            # 获取每一个n天以内的commit并打印出时间和拼接详情链接
            today = datetime.now()
            last_commit_date = time.mktime((today - timedelta(days=day_count)).timetuple())
            commits = repository.iter_commits(rev=None, paths='', max_age=last_commit_date)
            for commit in commits:
                result = {}
                commit_date = datetime.fromtimestamp(commit.committed_date)
                result['date'] = str(commit_date)
                result['committer'] = commit.author.name.encode('utf-8')
                # 需要对markdown的标签进行转义
                result['message'] = commit.message.replace('# ', '\# ') \
                    .replace('* ', "\* ") \
                    .replace('\r\n\r\n', ' >>> ') \
                    .replace('\n', '  ') \
                    .replace('\r', '  ') \
                    .split('Conflicts:')[0] \
                    .encode('utf-8')
                result['url'] = '{}/commit/{}'.format(repo['url'], str(commit))
                results.append(result)
            repo['commits'] = results
            if results == []:
                repo['error'] = '暂无更新'
        except Exception as e:
            repo['error'] = '仓库克隆失败，请检查是否仓库地址有误或是否有权限问题。仓库地址：{}'.format(repo['url'])
            print(str(e))
        summary.append(repo)
    return summary


# 生成对应格式的的message
def summaryToMarkdown(summary):
    message = ''
    for repo in summary:
        message += '#### {}：  \n'.format(repo['title'])
        message += '>  \n'
        if 'error' in repo.keys():
            message += repo['error'] + "\n\n"
            continue
        for commit in repo['commits']:
            message += '* 【{} **{}**】[{}]({})  \n'.format(commit['date'], commit['committer'], commit['message'],
                                                          commit['url'])
        message += '\n\n'
    return message


# 获取svn仓库代码commit情况 pysvnbot模块
def getCommitMessagesBySVN(repo, day_count):
    client = pysvn.Client()
    project_name = repo['url'].split('/')[-1]
    work_dir = os.path.join(tmp_path, project_name)
    lists = []
    message = ''
    try:
        # client.checkout(repo['url'], work_dir)
        print(project_name, '项目克隆完毕！！！')
        today = datetime.now()
        last_commit_date = time.mktime((today - timedelta(days=day_count)).timetuple())
        entries_list = client.log(repo['url'],
                                  revision_start=pysvn.Revision(pysvn.opt_revision_kind.head),
                                  revision_end=pysvn.Revision(pysvn.opt_revision_kind.number, 0), limit=0,
                                  discover_changed_paths=False, strict_node_history=True)
        for i in range(len(entries_list)):
            commit_date = entries_list[i].date
            if commit_date >= last_commit_date:
                commit_number = re.findall(r"\d+", str(entries_list[i].revision))[0]
                commit_message = entries_list[i].message
                commit_author = entries_list[i].author
                commits = {"commit_number": commit_number, "commit_message": commit_message,
                           "commit_author": commit_author,
                           "commit_date": str(datetime.fromtimestamp(commit_date))}
                lists.append(commits)
            else:
                continue
        if lists == []:
            lists.append({"error": "暂无更新"})
    except Exception as e:
        print(str(e))

    for commit in lists:
        message += '#### {}：  \n'.format(project_name)
        if 'error' in commit.keys():
            message += commit['error'] + "\n\n"
        else:
            message += '* 【{} **{}**】[{}]({})  \n'.format(commit['commit_number'], commit['commit_date'],
                                                      commit['commit_author'], commit['commit_message'])
            message += '\n\n'
    return message


CORPID = "wwfc2533e7f3ff1017"
CORPSECRET = "vktLymE_JcoXC0VcnsopwjLTY-dWpMadthQaFULnZ28"
BASEURL = 'https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={0}&corpsecret={1}'.format(CORPID, CORPSECRET)
URL = "https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token=%s"
class Token(object):
    def get_token(self):
        response = requests.request('GET', BASEURL).text
        result_json = json.loads(response)
        if result_json['errcode'] == 0:
            self.expire_time = time.time() + result_json['expires_in']
            self.access_token = result_json['access_token']
        return self.access_token


def send_message(title, content):
    team_token = Token().get_token()
    url = URL % (team_token)
    wechat_json = {
        # "toparty": "3",
        "touser":"HuangWenLiang",
        "msgtype": "text",
        "agentid": "1000002",
        "text": {
            "content": "title:{0}\n content:{1}".format(title, content)
        },
        "safe": "0"
    }
    response = requests.post(url, data=json.dumps(wechat_json, ensure_ascii=False).encode('utf-8'))
    print(response.text)



    # 获取文件信息
    def get_info(self, full_path, file_name):
        package = self.get_package(full_path)
        class_name = re.search('(\w+)\.java$', file_name).group(1)
        return (package, class_name)

    # 获取package包名
    def get_package(self, file_name):
        """获取package名"""
        ret = ''
        with open(file_name, encoding='utf-8') as fp:
            for line in fp:
                line = line.strip()
                match = re.match('package\s+(\S+);', line)
                if match:
                    ret = match.group(1)
                    break
        return ret


# if __name__ == '__main__':
    # ret = getCommitMessagesBySVN({"url":"svn://39.108.134.246/hlb/test/HttpRunnerManager-master"},100)
    # ret = getCommitMessagesByGit('{"url":"https://github.com/huangwenl/SprintNBA","branch":"master"}',90)
    # res = summaryToMarkdown(ret)
    # send_message("Jenkins构建报告", ret)
    # print(ret)

# {"url":"http://github.com/xx/xx","branch":"develop"}
# def get_login(realm, username, may_save):
#     return True, 'huangwenliang', 'huangwenliang356', True
#
# client = pysvn.Client()
# client.callback_get_login = get_login