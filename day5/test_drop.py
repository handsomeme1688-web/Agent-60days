# day5/test_drop.py

from practice import drop 

def test_drop_trims_long_history():
    msgs = [{"role":"system","content":"You are a helpful assistant"}]
    for i in range(15):
        msgs.append({"role":"user","content":"测试"*100})
        msgs.append({"role":"assistant","content":"回复"*100})
    result, ok = drop(msgs, 3000)
    assert ok is True                    # 应该裁剪成功，不是拒绝
    assert len(result) < 31              # 确实删掉了消息
    assert result[0]["role"] == "system" # system 还在