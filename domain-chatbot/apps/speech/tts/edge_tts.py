import logging
import os
import subprocess

from ..utils.uuid_generator import generate

logger = logging.getLogger(__name__)

edge_voices = [
    {"id": "zh-CN-XiaoxiaoNeural", "name": "xiaoxiao"},
    {"id": "zh-CN-XiaoyiNeural", "name": "xiaoyi"},
    {"id": "zh-CN-YunjianNeural", "name": "yunjian"},
    {"id": "zh-CN-YunxiNeural", "name": "yunxi"},
    {"id": "zh-CN-YunxiaNeural", "name": "yunxia"},
    {"id": "zh-CN-YunyangNeural", "name": "yunyang"},
    {"id": "zh-CN-liaoning-XiaobeiNeural", "name": "xiaobei"},
    {"id": "zh-CN-shaanxi-XiaoniNeural", "name": "xiaoni"},
    {"id": "zh-HK-HiuGaaiNeural", "name": "hiugaai"},
    {"id": "zh-HK-HiuMaanNeural", "name": "hiumaan"},
    {"id": "zh-HK-WanLungNeural", "name": "wanlung"},
    {"id": "zh-TW-HsiaoChenNeural", "name": "hsiaochen"},
    {"id": "zh-TW-HsiaoYuNeural", "name": "hsioayu"},
    {"id": "zh-TW-YunJheNeural", "name": "yunjhe"}
]


class Edge():

    def remove_html(self, text: str):
        # TODO 待改成正则
        new_text = text.replace('[', "")
        new_text = new_text.replace(']', "")
        return new_text

    def create_audio(self, text: str, voiceId: str):
        new_text = self.remove_html(text).strip()
        if not new_text:
            raise ValueError("edge-tts 输入文本为空，无法合成语音")
        pwdPath = os.getcwd()
        file_name = generate() + ".mp3"
        filePath = pwdPath + "/tmp/" + file_name
        dirPath = os.path.dirname(filePath)
        if not os.path.exists(dirPath):
            os.makedirs(dirPath)
        if not os.path.exists(filePath):
            # 用open创建文件 兼容mac
            open(filePath, 'a').close()

        result = subprocess.run(
            ["edge-tts", "--voice", voiceId, "--text", new_text, "--write-media", str(filePath)],
            capture_output=True,
            text=True
        )
        # 若调用失败或文件为空，抛出异常，避免返回静音文件
        if result.returncode != 0 or not os.path.exists(filePath) or os.path.getsize(filePath) == 0:
            logger.error("edge-tts 调用失败: code=%s stderr=%s", result.returncode, result.stderr)
            # 清理空文件，避免下游误认为成功
            if os.path.exists(filePath) and os.path.getsize(filePath) == 0:
                os.remove(filePath)
            raise RuntimeError("edge-tts 未返回音频，请检查网络/微软语音可用性或更换 TTS 类型")

        return file_name
