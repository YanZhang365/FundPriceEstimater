import traceback
import requests
import json
from config import CORP_ID, SECRET, TO_USER, AGENT_ID
import base64
import os
import hashlib

# 替换成你拿到的企业微信消息推送Webhook地址
WEBHOOK_URL = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=f5cd53f6-7c1d-496d-9994-347bc4c3791e"

def get_access_token():
    """自动获取token，增加异常捕获和结果校验"""
    try:
        url = f"https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={CORP_ID}&corpsecret={SECRET}"
        res = requests.get(url, timeout=10)  # 加超时，避免卡死
        res.raise_for_status()  # 触发HTTP错误（如404/500）
        token_data = res.json()

        # 校验token返回结果
        if token_data.get("errcode") != 0:
            print(f"❌ 获取Access Token失败：{token_data.get('errmsg')}（错误码：{token_data.get('errcode')}）")
            return None
        return token_data.get("access_token")

    except requests.exceptions.RequestException as e:
        print(f"❌ 获取Access Token网络异常：{str(e)}")
        return None
    except Exception as e:
        print(f"❌ 获取Access Token未知异常：{str(e)}")
        traceback.print_exc()  # 打印详细错误栈
        return None


def send_text_to_wechat(content):
    data = {
        "msgtype": "text",
        "text": {
            "content": content
        }
    }
    try:
        # 发送请求
        res = requests.post(
            WEBHOOK_URL,
            headers={"Content-Type": "application/json"},
            data=json.dumps(data),
            timeout=10
        )
        # 验证是否推送成功
        result = res.json()
        if result.get("errcode") == 0:
            print("✅ 微信推送成功！")
        else:
            print(f"❌ 推送失败：{result}")
    except Exception as e:
        print(f"❌ 推送异常：{str(e)}")


def send_html_to_wechat(html_content):
    """通用HTML推送函数，带完整异常捕获和结果校验"""
    # 1. 获取Token（先校验Token是否有效）
    token = get_access_token()
    if not token:
        print("❌ 无有效Access Token，终止推送")
        return False

    # 2. 构造请求参数
    url = f"https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={token}"
    data = {
        "touser": TO_USER,
        "agentid": AGENT_ID,  # 确保是整数（配置文件里要写数字，不是字符串）
        "msgtype": "html",
        "html": {"content": html_content},
        "safe": 0  # 0=普通消息，1=保密消息（可选）
    }

    try:
        # 3. 发送请求（加超时，避免卡死）
        headers = {"Content-Type": "application/json"}
        res = requests.post(
            url,
            data=json.dumps(data, ensure_ascii=False),  # ensure_ascii=False支持中文
            headers=headers,
            timeout=15
        )
        res.raise_for_status()  # 触发HTTP错误（如400/403/500）

        # 4. 解析返回结果（核心：校验企业微信接口的真实返回）
        result = res.json()
        if result.get("errcode") == 0:
            # 即使errcode=0，也要检查invaliduser/invalidparty（@all时可能有无效用户）
            invalid_user = result.get("invaliduser", "")
            invalid_party = result.get("invalidparty", "")

            if invalid_user or invalid_party:
                print(f"⚠️ 消息推送部分成功：")
                if invalid_user:
                    print(f"  - 无效用户ID：{invalid_user}（这些用户收不到消息）")
                if invalid_party:
                    print(f"  - 无效部门ID：{invalid_party}")
            else:
                print("✅ HTML消息推送完全成功！")
            return True

        # 5. 接口返回错误（errcode≠0）
        else:
            print(f"❌ 消息推送失败：")
            print(f"  - 错误码：{result.get('errcode')}")
            print(f"  - 错误信息：{result.get('errmsg')}")
            # 常见错误码提示（针对性指导）
            err_code = result.get('errcode')
            if err_code == 40035:
                print("  💡 原因：用户不在应用可见范围 → 检查应用「可见范围」配置")
            elif err_code == 45047:
                print("  💡 原因：日消息推送总量超限 → 减少推送频率")
            elif err_code == 45011:
                print("  💡 原因：接口调用频率超限 → 降低调用速度（≤300次/分钟）")
            elif err_code == 60011:
                print("  💡 原因：应用不可见 → 重新配置应用可见范围")
            return False

    # 6. 捕获网络异常（超时、连接失败等）
    except requests.exceptions.RequestException as e:
        print(f"❌ 消息推送网络异常：{str(e)}")
        traceback.print_exc()
        return False

    # 7. 捕获其他未知异常
    except Exception as e:
        print(f"❌ 消息推送未知异常：{str(e)}")
        traceback.print_exc()
        return False


def send_image_to_wechat(image_path):
    """
    发送本地图片到微信（支持企业微信机器人/应用）
    :param image_path: 本地图片路径（如"fund_report.png"）
    :return: 推送结果（True/False）
    """
    # 1. 校验文件存在
    if not os.path.exists(image_path):
        print(f"❌ 图片文件不存在：{image_path}")
        return False

    # 2. 读取图片并计算MD5+Base64（关键修改）
    try:
        with open(image_path, "rb") as f:
            image_data = f.read()  # 先读取二进制数据，避免重复读取
            # 计算MD5（32位小写）
            image_md5 = hashlib.md5(image_data).hexdigest()
            # 转Base64
            image_base64 = base64.b64encode(image_data).decode("utf-8")
    except Exception as e:
        print(f"❌ 读取/编码图片失败：{str(e)}")
        return False

    # 3. 构造参数（补充md5字段）
    data = {
        "msgtype": "image",
        "image": {
            "base64": image_base64,
            "md5": image_md5  # 必须填真实MD5，不能留空
        }
    }
    # 场景2：企业微信应用（替换上面的data，需结合access_token）
    # data = {
    #     "touser": "@all",
    #     "agentid": 1000001,
    #     "msgtype": "image",
    #     "image": {
    #         "base64": image_base64
    #     },
    #     "safe": 0
    # }

    # 4. 发送请求（完整异常处理）
    try:
        headers = {"Content-Type": "application/json"}
        res = requests.post(
            WEBHOOK_URL,
            headers=headers,
            data=json.dumps(data, ensure_ascii=False),
            timeout=15  # 延长超时，避免图片传输慢导致失败
        )
        res.raise_for_status()  # 触发HTTP错误（如400/403/500）

        # 5. 解析返回结果
        result = res.json()
        if result.get("errcode") == 0:
            print("✅ 图片推送成功！")
            return True
        else:
            print(f"❌ 图片推送失败：错误码{result.get('errcode')}，原因{result.get('errmsg')}")
            # 常见错误提示
            if result.get("errcode") == 41001:
                print("  💡 原因：缺少Access Token → 检查是否配置token（仅应用推送需要）")
            elif result.get("errcode") == 40003:
                print("  💡 原因：无效的用户ID → 检查touser配置")
            elif result.get("errcode") == 9001001:
                print("  💡 原因：图片Base64编码错误 → 检查图片文件是否损坏")
            return False

    # 网络异常（超时、连接失败等）
    except requests.exceptions.Timeout:
        print("❌ 推送超时：网络连接慢或微信接口响应超时")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ 推送失败：网络连接异常（如断网、Webhook地址错误）")
        return False
    except requests.exceptions.HTTPError as e:
        print(f"❌ 推送HTTP错误：{e.response.status_code} - {e.response.text}")
        return False
    # 其他未知异常
    except Exception as e:
        print(f"❌ 图片推送未知异常：{str(e)}")
        traceback.print_exc()
        return False


