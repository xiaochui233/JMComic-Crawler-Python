from jmcomic import *
from jmcomic.cl import JmcomicUI

# 下方填入你要下载的本子的id，一行一个，每行的首尾可以有空白字符
jm_albums = '''
jm495890
jm420339
jm382565
jm590277
jm419093
jm393526
jm486483
jm411743
jm419165
jm557462
jm324908
jm366792
jm589732
jm394674
jm407082
jm560611
jm354546
jm415616
jm594122
jm367010
jm408400
jm579795
jm413830
jm273257
jm317548
jm338411
jm368313
jm428359
jm378932
jm428369
jm420338
jm594762
jm416601
jm333733
jm583262
jm368489
jm564265
jm565029
jm570889
jm346838
jm369745
jm375639
jm369780
jm386951
jm413161
jm499833
jm577368
jm408082
jm420695
jm569566
jm447916
jm579247
jm595464
jm306372
jm347569
jm524946
jm368614
jm578718
jm357569
jm590312
jm397458
jm416654
jm305135
jm363801
jm580614
jm583013
jm570196
jm361002
jm568048
jm577501
jm402983
jm394328
jm575315
jm498691
jm500703
jm559091
jm426544
jm318900
jm421671
jm388981
jm428224
jm320715
jm574775
jm338391
jm412263
jm338383
jm591620
jm346515
jm410034
jm412541
jm365654
jm428371
jm592720
jm327671
jm353626
jm583249
jm376013
jm401889
jm411292
jm418529
jm419624
jm438577
jm449327
jm344545
jm388985
jm349038
jm411031
jm374044
jm368803
jm411008
jm418797
jm397468
jm560378
jm398695
jm562990
jm575036
jm525170
jm326314
jm369403
jm391880
jm403121
jm420730
jm392068
jm578519
jm346559
jm472567
jm569366
jm302261
jm314649
jm373408
jm578868
jm586521
jm419625
jm559493
jm584036
jm525559
jm548964
jm321363
jm373218
jm405787
jm294451
jm302214
jm369637
jm370735
jm403920
jm413152
jm408420
jm564414
jm575824
jm404955
jm590521
jm589005
jm407829
jm420977
jm427358
jm408066
jm589944
jm407830
jm590484
jm589009
jm407815
jm586503
jm576808
jm589955
jm386598
jm388384
jm399390
jm587861
jm559800
jm574905
jm416657
jm539405
jm391378
jm590274
jm564660
jm347438
jm368320
jm368633
jm420729
jm418820
jm383599
jm407783
jm589729
jm415666
jm416646
jm593610
jm392125
jm495967
jm373407




















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
