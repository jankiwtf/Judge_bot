kind_link = ['blue_site',
             'blue_site_v2',
             'brown_site',
             'brown_site_v2',
             'grey_site',
             'white_site'
             ]
blue_site = [
    'http://71.hbr.msudrf.ru',
    'http://2zlv.nsk.msudrf.ru',
    'http://6zlv.nsk.msudrf.ru',
    'http://dzer13.nnov.msudrf.ru',
    'http://27.perm.msudrf.ru',
    'http://23.sml.msudrf.ru',
    'http://suz2.wld.msudrf.ru',
    'http://156.mo.msudrf.ru'

]

blue_site_v2 = [
    'http://5.tula.msudrf.ru',
    'http://novotal2.iwn.msudrf.ru',
    'http://kir2-1.ros.msudrf.ru',
    'http://oktyabrsky2.pnz.msudrf.ru'
]

brown_site = [
    'https://norilsk--krk.sudrf.ru',
    'https://pgr--spb.sudrf.ru',
    'https://kirovsky--jrs.sudrf.ru',
    'https://maikopsky--adg.sudrf.ru',
    'https://msk--spb.sudrf.ru',
    'https://dser--vol.sudrf.ru',
    'https://krasnogorsk--mo.sudrf.ru',
    'https://ordzhonikidzevsky--svd.sudrf.ru',
    'https://berdsky--nsk.sudrf.ru',
]

brown_site_v2 = [
    'https://9kas.sudrf.ru',
    'https://1kas.sudrf.ru',
    'https://2kas.sudrf.ru',
    'https://3kas.sudrf.ru',
]

# brown_site_short = [
#     'http://leninsky.bkr.sudrf.ru',
# ]

grey_site = [
    'https://mirsud.spb.ru',
]

white_site = [
    'https://mos-sud.ru',
    'https://mos-gorsud.ru'
]

# red_site = [
#     'https://ms83.mirsud24.ru',
# ]

green_site = [
    'http://mirsud.tatar.ru',
]

# Search link in DB
def where_url_save(url):
    indx_slash = url.find('/', 8)
    short_link = url[:indx_slash]
    if short_link in blue_site:
        return 'blue_site'
    elif short_link in blue_site_v2:
        return 'blue_site_v2'
    elif short_link in brown_site:
        return 'brown_site'
    elif short_link in brown_site_v2:
        return 'brown_site_v2'
    # elif short_link in brown_site_short:
        # return 'brown_site_short'
    elif short_link in grey_site:
        return 'grey_site'
    elif short_link in white_site:
        return 'white_site'
    # elif short_link in red_site:
    #     return 'red_site'
    elif short_link in green_site:
        return 'green_site'
    else:
        return False
