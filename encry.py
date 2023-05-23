from Cryptodome.Cipher import AES
import base64


def get_singnature(text):
    """
    获取加密的text参数
    :param text:当前的时间戳
    :return:经过AES加密后的密文
    """
    # 密钥
    key = "6f00cd9cade84e52"
    # 偏移量
    iv = "25d82196341548ef"
    pad = 16 - len(text) % 16
    # 填充模式设置为了r.a.pad.Pkcs7
    text = str(text) + pad * chr(pad)
    encryptor = AES.new(key.encode("UTF8"), AES.MODE_CBC, iv.encode("UTF8"))
    result = encryptor.encrypt(text.encode("UTF8"))
    # 因为AES加密时候得到的字符串不一定是ascii字符集的，输出到终端或者保存时候可能存在问题
    # 所以这里统一把加密后的字符串转化为16进制字符串
    rdd = base64.b64encode(result).decode("UTF8")
    return rdd

if __name__ == '__main__':
    currentTime = str(1683426681869)
    print(currentTime)
    print(get_singnature(currentTime))