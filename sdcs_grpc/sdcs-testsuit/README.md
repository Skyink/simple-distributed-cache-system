<!--
 * @Author: ringfall linfp21@126.com
 * @LastEditTime: 2023-10-06 13:01:57
 * @Description: 
 * 
 * Copyright (c) 2023 by Peng-LinFeng, All Rights Reserved. 
-->
# sdcs-testsuit
Simple test for SDCS

```sh
./sdcs-test.sh {cache_server_number}
```

## Todo
- [ ] Real performance test (by jmeter?)
- [ ] Better command line argument processing and help.

## Q&A
1. Mac用户运行脚本时提示`shuf: command not found`，是因为系统缺少相关指令工具。
  - 解决方案：通过`brew install coreutils`安装相应的工具。
1. Mac用户运行脚本时提示`syntax error in expression(xxx)`或`declare: -A: invalid option`的错误，是bash版本过低导致。本测试脚本需要bash4及以上可以正常运行。Mac出厂自带的bash版本为3.2。
  - 解决方案：
    1. 使用homebrew安装新版本的bash。使用`brew install bash`更新bash。
    2. 安装完成后使用`which -a bash`指令查看bash路径。可以看到两个地址：`/bin/bash`是Mac出厂自带的bash，另一个是新安装的bash。请使用自己安装的bash进行操作。
       ```sh
       /usr/local/bin/bash    # 新安装的bash，可能是其他路径如 /opt/homebrew/bin/bash
       /bin/bash              # Mac出厂自带的bash
       ```
    3. 可以通过`/usr/local/bin/bash --version`确认新bash的版本。
    4. 使用`/usr/local/bin/bash ./sdcs-test.sh {cache_server_number}`运行测试脚本。


