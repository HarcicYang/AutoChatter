import google.generativeai as genai
from google.generativeai import GenerationConfig
from google.generativeai.types import HarmCategory, HarmBlockThreshold
import json

from ct.utils.config import ChatterConfig
from ct.events import Event
from ct.actions import Action, NoneArgs, MsgSendArgs

cfg: ChatterConfig = ChatterConfig.get("otto-chatter")
base_prompt = \
    """
    从现在开始，你的一切回答都应当使用json格式，具体格式如下：
    {action: action, args: {arg1: value1, arg2: value2, arg3: value3, ...}}
    其中：
     - action: 操作名称，类型为string;
     - args: 参数
     
    可选的action的值以及其他要求如下：
    
    0. 什么也不做
        action: none
        args: {}
        其中：
         - action为str类型的"none"
    
    1. 消息发送
        action: send_msg
        args: ｛gid: gid, at: true/false, reply: true/false, msgs: [msg_scope1, delay_1, msg_scope2, delay_2, ...], emotion_change: n}
        其中：
         - 在收到消息时，你应当*自行选择是否回复该消息*，若不回复，请使用操作0: 什么也不做；
         - gid为将要发送消息的目标群号, type int;
         - at标志是否在回复消息时对被回复消息的发送者进行at， bool;
         - reply标志是否在回复消息时对被回复消息进行引用， bool;
         - at和reply可以同时为false，但是不能同时为true
         - 你应当回答尽可能短的消息，回答是应当考虑真实人类的打字速度以及知识边界问题。若回答较长（len>=15），则应当拆分为多个较短的scope，每两个scope间间隔一个delay，该delay单位为秒，类型为float，代表下一条消息需要在随后的延迟后被显示（以真实人类打字速度以及语段意义之间的连续与非连续性为基准）。若只有一个scope，则不需要delay。若scope数量在2个及以上，则必须在每个scope之间插入一个delay，类型为float，不要使用引号包裹。
         - emotion_change为当前情绪值的改变量，应为float，为正是增加，为负减小。
         - 回答时只提供json内容，不要包含其他任何内容，也不要使用任何的标记格式（如markdown）
        
        at和reply如何恰当使用：
         - at和reply一般适用于两条聊天记录相隔很远时；
         - reply也可以用于明确指向要标记的消息，而at不能；
         - 一般连续性聊天应当在中途较少使用at和reply，但是在开启一次聊天时，建议使用reply或at；
         - at和reply都很适合开启一段新的聊天
        
        其他注意：
         - 是否回复消息应当收到以下因素影响：
            1. 你对于聊天内容是否感兴趣；
            2. 这条消息的主题/内容是否和正在进行的聊天相关；
            3. 当前心情值（回复的语句长度、语气等也于此有关）
    
    
    对于一切提问，均遵循以下json格式：
    {event: event_type, body: {...}}
    其中：
     - event为事件类型
     - body为事件内容
     
    可能的event如下：
    
    1. 收到消息
        event: msg_received
        body: {sender: {nickname: name, uin: uin}, gid: gid, reply_to: msg/null, msg: ["...", "...", ...], emotion: n}
        其中：
         - sender为发送者信息，其下nickname为发送者昵称；uin为发送者qq号；
         - gid为该消息来自的群的群号；
         - msg是消息内容，类型list[str]；
         - reply_to为这条消息发送时引用的消息，如果没有则为null;
         - emotion为当前心情值, [0, 100]
    
    以下是你的角色信息：
    
    """

genai.configure(api_key=cfg.chatting.api_key)


class ChatAPI:
    def __init__(self):
        self.model = genai.GenerativeModel(
            model_name="gemini-1.5-flash-002",
            generation_config=GenerationConfig(
                temperature=1.5,
                top_p=0.95,
                top_k=40,
                max_output_tokens=8192,
                response_mime_type="text/plain"
            ),
            safety_settings={
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE
            },
            system_instruction=base_prompt + cfg.chatting.prompt
        )

        self.session = self.model.start_chat()

    @property
    def tools(self):
        class Tools:
            pass

        return Tools()

    def gen(self, ev: Event) -> Action:
        print(ev)
        event = ev.to_json()
        rsp = json.loads(self.session.send_message(json.dumps(event)).text.replace("```json", "").replace("```", ""))
        if rsp["action"] == "none":
            return Action(
                "none", NoneArgs()
            )
        elif rsp["action"] == "send_msg":
            return Action(
                "send_msg",
                MsgSendArgs(
                    gid=int(rsp["args"]["gid"]),
                    at=rsp["args"]["at"],
                    reply=rsp["args"]["reply"],
                    msgs=rsp["args"]["msgs"],
                    emotion_change=rsp["args"]["emotion_change"]
                )
            )
        else:
            raise NotImplementedError
