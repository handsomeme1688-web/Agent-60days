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
    
    
def test_drop_keeps_short_history_unchanged():
    """边界：没超限时应原样返回，不裁剪"""
    msgs = [{"role":"system","content":"sys"},
            {"role":"user","content":"你好"}]
    result, ok = drop(msgs, 3000)
    assert ok is True
    assert len(result) == 2          # 一条都没删

def test_drop_rejects_oversized_single_message():
    """异常：单条消息大到装不下时应拒绝"""
    msgs = [{"role":"system","content":"sys"},
            {"role":"user","content":"啊"*6000}]   # 远超3000 token
    result, ok = drop(msgs, 3000)
    assert ok is False               # 拒绝，而不是裁剪