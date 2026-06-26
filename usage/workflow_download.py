from jmcomic import *
from jmcomic.cl import JmcomicUI

# 下方填入你要下载的本子的id，一行一个，每行的首尾可以有空白字符
jm_albums = '''
jm337384
jm213541
jm213946
jm1209059
jm1208710
jm1208696
jm1208695
jm1208686
jm1208682
jm1208410
jm1208375
jm1208401
jm1208370
jm1208342
jm1208277
jm1208258
jm1208124
jm1208036
jm1207923
jm1207922
jm1207920
jm1207868
jm1207849
jm1207821
jm1207808
jm1207796
jm1207713
jm1207678
jm1207464
jm1207463
jm1207461
jm1207447
jm1207393
jm1102269
jm1207208
jm1207157
jm1206730
jm1206683
jm1206620
jm1206619
jm1206617
jm616107
jm1206609
jm1206438
jm1206295
jm1206236
jm1206219
jm1206214
jm1205989
jm1205967
jm1205955
jm1205949
jm1205856
jm1205844
jm1205828
jm1205358
jm1205294
jm1205184
jm1205181
jm1204970
jm1204723
jm1204542
jm1204527
jm1204276
jm1204074
jm1204071
jm1204061
jm1204060
jm1204059
jm1204044
jm1204036
jm1203830






















'''

# 单独下载章节
jm_photos = '''



'''


def env(name, default, trim=('[]', '""', "''")):
    import os
    value = os.getenv(name, None)
    if value is None or value == '':
        return default

    for pair in trim:
        if value.startswith(pair[0]) and value.endswith(pair[1]):
            value = value[1:-1]

    return value


def get_id_set(env_name, given):
    aid_set = set()
    for text in [
        given,
        (env(env_name, '')).replace('-', '\n'),
    ]:
        aid_set.update(str_to_set(text))

    return aid_set


def main():
    album_id_set = get_id_set('JM_ALBUM_IDS', jm_albums)
    photo_id_set = get_id_set('JM_PHOTO_IDS', jm_photos)

    helper = JmcomicUI()
    helper.album_id_list = list(album_id_set)
    helper.photo_id_list = list(photo_id_set)

    option = get_option()
    helper.run(option)
    option.call_all_plugin('after_download')


def get_option():
    # 读取 option 配置文件
    option = create_option(os.path.abspath(os.path.join(__file__, '../../assets/option/option_workflow_download.yml')))

    # 支持工作流覆盖配置文件的配置
    cover_option_config(option)

    # 把请求错误的html下载到文件，方便GitHub Actions下载查看日志
    log_before_raise()

    return option


def cover_option_config(option: JmOption):
    dir_rule = env('DIR_RULE', None)
    if dir_rule is not None:
        the_old = option.dir_rule
        the_new = DirRule(dir_rule, base_dir=the_old.base_dir)
        option.dir_rule = the_new

    impl = env('CLIENT_IMPL', None)
    if impl is not None:
        option.client.impl = impl

    suffix = env('IMAGE_SUFFIX', None)
    if suffix is not None:
        option.download.image.suffix = fix_suffix(suffix)

    pdf_option = env('PDF_OPTION', None)
    if pdf_option and pdf_option != '否':
        call_when = 'after_album' if pdf_option == '是 | 本子维度合并pdf' else 'after_photo'
        
        pdf_name_rule = env('PDF_NAME_RULE', None)
        if isinstance(pdf_name_rule, str):
            pdf_name_rule = pdf_name_rule.strip()
            
        if not pdf_name_rule:
            pdf_name_rule = '[JM{Aid}] {Atitle}' if call_when == 'after_album' else '[JM{Aid}] 第{Pindex}章-JM{Pid}-{Ptitle}'
            
        plugin = [{
            'plugin': Img2pdfPlugin.plugin_key,
            'kwargs': {
                'pdf_dir': option.dir_rule.base_dir + '/pdf/',
                'filename_rule': pdf_name_rule,
                'delete_original_file': True,
            }
        }]
        option.plugins[call_when] = plugin


def log_before_raise():
    jm_download_dir = env('JM_DOWNLOAD_DIR', workspace())
    mkdir_if_not_exists(jm_download_dir)

    def decide_filepath(e):
        resp = e.context.get(ExceptionTool.CONTEXT_KEY_RESP, None)

        if resp is None:
            suffix = str(time_stamp())
        else:
            suffix = resp.url

        name = '-'.join(
            fix_windir_name(it)
            for it in [
                e.description,
                current_thread().name,
                suffix
            ]
        )

        path = f'{jm_download_dir}/【出错了】{name}.log'
        return path

    def exception_listener(e: JmcomicException):
        """
        异常监听器，实现了在 GitHub Actions 下，把请求错误的信息下载到文件，方便调试和通知使用者
        """
        # 决定要写入的文件路径
        path = decide_filepath(e)

        # 准备内容
        content = [
            str(type(e)),
            e.msg,
        ]
        for k, v in e.context.items():
            content.append(f'{k}: {v}')

        # resp.text
        resp = e.context.get(ExceptionTool.CONTEXT_KEY_RESP, None)
        if resp:
            content.append(f'响应文本: {resp.text}')

        # 写文件
        write_text(path, '\n'.join(content))

    JmModuleConfig.register_exception_listener(JmcomicException, exception_listener)


if __name__ == '__main__':
    main()
