import asyncio
import time

async def execute_shell_command(command): 
    process = await asyncio.create_subprocess_shell(command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)   
    stdout, stderr = await process.communicate() 
    return stdout, stderr

cmd='echo \'你好\' |   E:\\MET\\MET-system\\ws-server\\tts\\piper\\piper.exe -m E:\\MET\\MET-system\\ws-server\\tts\\piper\\zh_CN-huayan-medium.onnx -c E:\\MET\\MET-system\\ws-server\\tts\\piper\\zh_CN-huayan-medium.onnx.json -f E:\\MET\\MET-system\\ws-server\\tts\\voice\\{}.wav'.format(time.time()) 
# 保证cmd以utf-8编码
cmd = cmd.encode('utf-8').decode('utf-8')
stdout, stderr = asyncio.run(execute_shell_command(cmd))

print(stdout)
print(stderr)

