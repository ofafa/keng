# proposal loader
'''
parse the proposal data from raw markdown file
'''

import re
import jieba
import pandas as pd
import numpy as np
from collections import Counter

title_header = ['##', '案名']
proposer_header = ['提案人', '坑主', '執行人']
recruiting_header = ['需要', '簡短坑表', '適合跳坑的人']

title_pattern = ".*##|案名.*"

patterns = {
    'title': "#{2}[^#].*|案名.*",
    'proposer': "提案人|坑主|執行人.*",
    'recruiting': "- \[ \] ",
    'recruited': "- \[x\] "
}

stopwords = 'a|▶|的|，|-|/|。|\.|\*|,|、|人|:|是|\(|\)|在|有|可以|the|：|了|做|我|and|to|我們|這個|一個|坑表|與|和|說|讓|簡短|\[|\]|\"|也|大家|到|為|或|不|把|？|（|）| |他|比|對|這是|of|跟|要|..%|＃|“|都|於|%|#+|`|你'

keyword_categories = {
    'data': ['python', 'data scientist', 'data engineer', '資料', 'data'],
    'web': ['seo', 'frontend', 'backend', 'javascript', 'web', '前端工程師', '後端工程師', '設計', 'UI'],
    'health': ['medical', 'healthcare', 'health'],
    'sports': ['tennis', 'outdoor activities', 'snow boarding']
}


def encoding_categories(array):
    res = np.zeros((len(array), len(keyword_categories)))
    #cats = list(keyword_categories.keys())
    cats_contents = list(keyword_categories.values())

    # array = [['python', 'data'], 
    #          ['javascript', 'seo'], 
    #          ['test', 'hello']]

    for i in range(len(array)):
        for j in range(len(cats_contents)):
            for k in array[i]:
                if k in cats_contents[j]:
                    res[i][j] += 1
    return res


def search(name, type, users, projs):
    if name not in users:
        return None
    if type == 'user':
        return None


def setup(proj_file_path, user_profile_path):
    projs = load_projs(proj_file_path)
    tf, projs = aggregate_keywords(projs)
    users = pd.read_csv(user_profile_path)
    ud = {u['Name'].lower(): u for u in users.to_dict(orient='record')}
    uk = [[x['#1 keyword '].lower(), x['#2 keyword '].lower(), x['#3 keyword '].lower()] for x in ud.values()]
    pks = []
    for p in projs:
        tmp = [x[0] for x in p['keywords']] if 'keywords' in p else []
        tmp += p['recruiting'] if 'recruiting' in p else []
        pks.append(tmp)
    return {'tf': tf, 'projs': projs, 'ud': ud, 'uk': uk, 'pks': pks, 
            'euk': encoding_categories(uk), 'epks': encoding_categories(pks)}

def compute_mat(tmp):
    return np.dot(tmp['euk'], np.transpose(tmp['epks']))

def load_projs(path):
    lines = open(path).readlines()
    projs = []
    proj = dict()
    proj['meta'] = list()
    for l in lines:
        l = l.replace('\n', '')
        added = False
        for k in patterns.keys():
            if (re.match(patterns[k], l) is not None) and k == 'title':
                if len(proj.keys()) > 1:
                    projs.append(proj)
                    proj = dict()
                    proj['meta'] = list()
                tokens = re.split(' ', l)
                if len(tokens) > 1:
                    proj[k] = ' '.join(tokens[1:])
                    added = True
            elif (re.match(patterns[k], l) is not None) and k == 'proposer':
                tokens = re.split(':|：| ', l)
                if len(tokens) > 1:
                    proj[k] = ' '.join(tokens[1:])
                    added = True
            elif (re.match(patterns[k], l) is not None) and k == 'recruiting' or k == 'recruited':
                tokens = re.split(patterns[k], l)
                if len(tokens) > 1:
                    if k not in proj: 
                        proj[k] = list()
                    proj[k].append(' '.join([x.lower() for x in tokens[1:]]))
                    added = True
        if l != '' and added == False:
            proj['meta'].append(l.lower())
    return projs


def aggregate_keywords(projs):
    tf_all = Counter()
    for i in range(len(projs)):
        corpus = ' '.join(projs[i]['meta'])
        tokens = list(jieba.cut(corpus))
        tokens = list(filter(None, [k if re.match(stopwords, k) is None else None for k in tokens]))
        c = Counter(tokens)
        for k in c:
            if k in tf_all:
                tf_all[k] += c[k]
            else:
                tf_all[k] = c[k]
            projs[i]['keywords'] = c.most_common(10)
    return tf_all, projs



