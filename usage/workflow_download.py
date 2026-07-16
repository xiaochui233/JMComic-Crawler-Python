from jmcomic import *
from jmcomic.cl import JmcomicUI

# 下方填入你要下载的本子的id，一行一个，每行的首尾可以有空白字符
jm_albums = '''
jm1203821
jm1203802
jm1203801
jm1203784
jm1203751
jm1203555
jm1203478
jm1203462
jm1203479
jm1203524
jm1203256
jm1203373
jm1203372
jm1203222
jm1203255
jm1203269
jm1203258
jm1203277
jm1203236
jm1203283
jm1203252
jm1203039
jm1202987
jm1073315
jm641316
jm1202697
jm1202705
jm1202696
jm1202709
jm1202686
jm504439
jm1202600
jm1202591
jm1202580
jm1202576
jm1202437
jm1202351
jm1202349
jm586874
jm1201936
jm1201562
jm1201684
jm1201562
jm1201435
jm1201212
jm1201388
jm1201423
jm1201391
jm1201221
jm1201217
jm1201118
jm1200930
jm1200902
jm1200954
jm1200970
jm1200977
jm1200983
jm1200985
jm1200877
jm1200470
jm1200375
jm1196923
jm1200269
jm1205189
jm1200270
jm642229
jm1200128
jm1200156
jm1200159
jm1200177
jm1200179
jm1200182
jm1199886
jm350788
jm1199763
jm1199672
jm1199873
jm1199732
jm1199731
jm1199703
jm540704
jm1199708
jm1199529
jm1083967
jm1083979
jm1083382
jm1083003
jm1079695
jm1082819
jm1081256
jm1081342
jm1081550
jm1081268
jm1080564
jm1079708
jm1081254
jm1079939
jm1079731
jm1080329
jm1079725
jm1076890
jm1077772
jm418973
jm1074021
jm1074022
jm1073198
jm1069579
jm1072730
jm1071977
jm1072134
jm1184667
jm641338
jm515064
jm1069065
jm1069066
jm1209292
jm1067720
jm1067643
jm1066976
jm281146
jm1065213
jm1066361
jm1065030
jm1063432
jm1062482
jm1042940
jm1060955
jm1055313
jm1059013
jm1058187
jm1059753
jm1058185
jm1058178
jm1054780
jm1063140
jm1050067
jm496525
jm1050130
jm1045602
jm1049680
jm1179072
jm1042944
jm1045447
jm1045410
jm1042867
jm542765
jm1041359
jm1040849
jm1036183
jm1036185
jm1040326
jm1038951
jm1038991
jm1038275
jm1039514
jm1037952
jm1038318
jm1035108
jm1036722
jm463493





















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
