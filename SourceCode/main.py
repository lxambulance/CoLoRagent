# 主调度进程
import ColorMonitor as CM

if __name__ == '__main__':
    
    CM.PL.Nid = 1
    CM.PL.AddCacheSidUnit('F:\\研一下\\系统搭建\\代码实现\\test1.txt',1,0,0,0)
    CM.PL.AddCacheSidUnit('F:\\研一下\\系统搭建\\代码实现\\kebiao.png',1,0,0,0)
    CM.PL.SidAnn()
    
    thread_monitor = CM.Monitor()
    thread_monitor.start()