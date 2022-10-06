# git使用

## 基本操作

文件操作

```shell
git add/rm file/folder # 文件（文件夹）在暂存区添加/删除
git commit -m "message" # 提交到本地版本库
git checkout --filename # 撤销工作区文件修改
git reset HEAD filename # 撤销暂存区文件修改
git diff filename # 比较文件修改，先比较暂存区，没有时比较工作区
```

查看操作

```shell
git status # 查看工作区修改情况
git log # 查看git历史信息
git log --oneline # 一行简洁显示历史信息
git log --graph # 显示对应合并分支图
```

分支管理

```shell
git branch name # 创建分支，-d删除
git checkout name # 切换分支，-b创建且切换
git merge name # 将name分支与当前所在分支合并，此时默认会触发快速合并，加--no-ff可以关闭
```

连接github

```shell
git config --global user.email "email" # 设置本地全局用户邮箱
git config --global user.name "name" # 设置本地全局用户名
ssh-keygen -t rsa -C "email" # 生成ssh密钥，加密算法可换，生成的公钥文件内容需要添加到github网站方可正常访问。
ssh -v git@github.com # ssh连接测试
```

远程库管理

```shell
git remote -v # 显示远程库绑定情况
git remote rename a b # 将远程库a改名为b，因为默认clone远程库名为origin，添加其他远程库之前最好先改名
git remote add git_address # 增加远程库关联
git clone git_address # 克隆远程库，默认下载master分支
git checkout -b dev origin/dev # 新建并连接本地库dev与远程库dev
git branch --set-upstream-to dev origin/dev # 连接远端库与本地库，远程库默认名origin，可以git remote rename改名
git branch -vv # 查看远程库与本地库连接情况
git branch -a #查看所有分支，包括远程库
git push --set-upstream origin test # 将当前分支推送到远程test分支
git push origin --delete test # 将远程test分支删除
```

设置命令别名

```shell
git config --global alias.lg "log --color --graph --pretty=format:'%Cred%h%Creset -%C(yellow)%d%Creset %s %Cgreen(%cr) %C(bold blue)<%an>%Creset' --abbrev-commit"
```

git标签

```shell
git tag # 列出已有的标签信息
# git中有两种标签，附注标签是一条完整的记录，轻量标签用于临时打标记
git tag -a version -m "这是一条附注标签" # 完整的附注标签
git tag version # 轻量标签
git tag -a version 9fceb02 # 可以给以前的某次提交打上标签，方便后续查找
# 标签可以像分支操作一样引出其他分支
git checkout -b test v1.0 # 从tag v1.0引出分支test，这是一种比较常用的测试法
git push origin version # 推送tag到远程库
git push origin --tags # 推送本地所有tag到远程库
```

本地库目录下创建.gitignore 文件，然后把要忽略的文件名填进去，Git 就会自动忽略这些文件。

## 多人协作流程

主分支master，开发分支dev只有一个。只上传dev分支，master分支视dev分支完成情况合并。

dev分支clone到本地后新建自己的分支，代码完事后合并到dev分支然后提交。个人分支需要多机备份，可以在远程库创建个人personal分支来同步。基本工作流如下

### 配置远程库密钥

首先配置github的ssh公钥，使得本地拥有远程库读写权限。

本地生成密钥命令如下

```shell
ssh-keygen [ -t dsa | ecdsa | ecdsa-sk | ed25519 | ed25519-sk | rsa] -C "your email"
```

登录github，将本地生成的密钥.ssh/key.pub中内容添加到github密钥设置中。

### 配置本地库

修改本地.ssh/config配置文件，添加类似如下内容（github注意Perfer...那行，否则无法测试）

```shell
Host github.com
  HostName ssh.github.com
  User your email
  Port 443
  PreferredAuthentications publickey
  IdentitiesOnly yes
  IdentityFile ~\.ssh\id_xxx
```

### 远程库连接测试

注意需要再次确认是否设置git配置，git config global...。

测试连接命令如下（注意用户名为git）

```shell
ssh -v git@github.com
# 返回Hi提示即连接正常
```

### 获取代码

第一次拉取代码命令

```shell
git clone git_address # 默认下载默认库
git checkout -b dev origin/dev
```

### 修改、冲突

修改后提交

```shell
git push origin dev # dev是远程库对应分支名
```

出现冲突

```shell
git pull --rebase # 建议加rebase，这样简单的修改（不涉及到他人代码部分）直接变成一条分支，显示效果比较好
```

修改完冲突后再次正常提交即可。奇怪的分支操作具体参见上一小节中的远程库操作

## commit提交建议格式

不设限，可以尽量多写一些改动说明。**禁止空的commit**。

基本格式`<type>(<scope>):<subject>`

```text
type(必须项)
feat：新功能（feature）。
fix/to：修复bug，可以是QA发现的BUG，也可以是研发自己发现的BUG。
	fix：产生diff并自动修复此问题。适合于一次提交直接修复问题
	to：只产生diff不自动修复此问题。适合于多次提交。最终修复问题提交时使用fix
docs：文档（documentation）。
style：格式（不影响代码运行的变动）。
refactor：重构（即不是新增功能，也不是修改bug的代码变动）。
perf：优化相关，比如提升性能、体验。
test：增加测试。
chore：构建过程或辅助工具的变动。
revert：回滚到上一个版本。
merge：代码合并。
sync：同步主线或分支的Bug。

scope(可选项)
scope用于说明 commit 影响的范围，比如数据层、控制层、视图层等等，视项目不同而不同。
例如在Angular，可以是location，browser，compile，compile，rootScope， ngHref，ngClick，ngView等。如果你的修改影响了不止一个scope，你可以使用*代替。
若项目中没有太大的架构，可以指明文件替代。

subject(必须项)
subject是commit目的的简短描述，不超过50个字符。
建议使用中文（感觉中国人用中文描述问题能更清楚一些）。
结尾不加句号或其他标点符号。
```

### 范例

fix(DAO):用户查询缺少username属性

feat(Controller):用户查询接口开发

## 特殊需求：如何永久删除错误提交文件

在一个历史提交中错误提交文件，但是许久后发现，现在需要去除该文件影响（本项目中前期错误地将一个100+MB的打包工程文件提交到了代码库中，导致后续clone都需要先下载100+MB，而实际代码5MB不到）。

1. 从历史中永久删除文件。此时提交记录hash需要重新计算，过程较慢。

```shell
git filter-branch --force --index-filter 'git rm --cached --ignore-unmatch path-to-your-remove-file' --prune-empty --tag-name-filter cat -- --all
```

2. 强制推送修改到远程库

```shell
git push origin master --force
git push origin master --force --tags
```

3. 清理和回收本地空间

```shell
rm -rf .git/refs/original/
git reflog expire --expire=now --all
git gc --prune=now
git gc --aggressive --prune=now
```
