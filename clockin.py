import selenium
from selenium import webdriver
from time import sleep
from datetime import datetime, timedelta
import traceback
import platform
import json
from selenium.webdriver.common.by import By
from os import path
# fallback values for settings.json
retrymax=2
printToConsole=True
silent=False
chromeBinaryPath=None
logSucceededRecord=True
savePath=None
loginURL = 'https://pass.sdu.edu.cn/cas/login'
requestURL_left = 'https://scenter.sdu.edu.cn/tp_fp/view?m=fp#from=hall&serveID=41d9ad4a-f681-4872-a400-20a3b606d399&act=fp/serveapply'
requestURL_not_left = 'https://scenter.sdu.edu.cn/tp_fp/view?m=fp#from=hall&serveID=e027d752-0cbc-4d83-a9d5-1692441e8252&act=fp/serveapply'
# end fallback values
try:
    f=open("users.json",encoding="utf8")
    log=open("log.txt","a")
    users=json.load(f)

except:
    log.close()
    exit(-1)
finally:
    f.close()

try:
    s=open("settings.json",encoding="utf8")
    settings=json.load(s)
    if "chrome" in settings:chromeBinaryPath=settings["chrome"]
    if "retrymax" in settings:retrymax= settings["retrymax"]
    if "silent" in settings:silent= settings["silent"]
    if "logsucceeded" in settings:logSucceededRecord= settings["logsucceeded"]
    if "print2con" in settings:printToConsole= settings["print2con"]
    if "save_path" in settings:savePath= settings["save_path"]
except:
    if printToConsole:print("settings.json not found or corrupted. Use default settings.")
finally:s.close()
def writelog(msg):
    log.write(msg)
    if printToConsole:print(msg)
if not users:
    writelog("Warning : no users in users.txt\nApp exiting.\n")
    sleep(5)
    exit(1)
options=webdriver.ChromeOptions()
#mobileEmulation = {'deviceName': 'iPhone X'}
#options.add_experimental_option('mobileEmulation', mobileEmulation)
options.add_argument('--no-sandbox')
options.add_argument('--disable-gpu')
options.add_argument('--hide-scrollbars')
options.add_argument('blink-settings=imagesEnabled=false')
options.add_argument('--disable-dev-shm-usage')
if silent:
    options.add_argument('--headless')
if chromeBinaryPath:
    options.binary_location= chromeBinaryPath

def save_screenshot(driver,user):
    if not savePath:
        return
    try:
        driver.get("about:blank")
        driver.get("https://scenter.sdu.edu.cn/tp_fp/view?m=fp#act=fp/myserviceapply/indexFinish")
        driver.implicitly_wait(10)
        js_top = "var q=document.documentElement.scrollTop=0"
        driver.execute_script(js_top)
        spath = path.join(savePath,user['username']+".png")
        sleep(8)
        succeeded=driver.save_screenshot(spath)
        if not succeeded:
            writelog(f"Screenshot of {user['username']} failed @ {datetime.now()} without specific error messages. Please check if the path exists or if you have permission issues.")
    except Exception as e:
        writelog(f"===== Screenshot Error Begin @ {datetime.now()} =====")
        writelog(f"Error occurred while taking or saving screenshot , User = {user['username']}.\nStack Trace:{traceback.format_exc()}\n")
        writelog(f"===== Screenshot Error End @ {datetime.now()} =====")

if __name__ == '__main__':
    for user in users:
        for i in range(retrymax):
            try:
                driver=webdriver.Chrome( "chromedriver.exe" if platform.system()=="Windows" else"./chromedriver",chrome_options=options)
                driver.get(loginURL)
                driver.set_window_size(375,812)
                driver.implicitly_wait(6)
                username=driver.find_element_by_id("un")
                password=driver.find_element_by_id("pd")
                username.send_keys(user['username'])
                password.send_keys(user['password'])
                driver.implicitly_wait(2)
                submit = driver.find_element_by_id("index_login_btn")
                submit.click()
                driver.implicitly_wait(5)
                driver.get(requestURL_left if user['left'] else requestURL_not_left)
                driver.implicitly_wait(5)
                already_clocked_in = False
                for t in range(10):
                    try:
                        alert = driver.switch_to.alert
                        already_clocked_in = True
                        alert.accept()
                        save_screenshot(driver,user)
                        if logSucceededRecord:writelog(f"Already clocked in, user {user['username']} , time {datetime.now()}\n")
                        break
                    except:
                        sleep(2)
                if already_clocked_in: break
                driver.find_element(By.CSS_SELECTOR, ".layui-layer-content #mag_take_cancel").click()
                sleep(3)
                driver.switch_to.frame(1)
                if user['left']:
                    driver.implicitly_wait(10)
                    dtn = datetime.now() - timedelta(days=1) 
                    test_time = driver.find_element_by_id('CLSJ')
                    test_time.clear()
                    test_time.send_keys(dtn.strftime("%Y-%m-%d %H:%M:%S"))

                    driver.find_element(By.CSS_SELECTOR, ".btn-group:nth-child(2) .filter-option").click()
                    sleep(3)
                    driver.find_element(By.LINK_TEXT, user['province']).click()

                    driver.find_element(By.CSS_SELECTOR, ".btn-group:nth-child(5) .filter-option").click()
                    sleep(3)
                    driver.find_element(By.LINK_TEXT, user['city']).click()

                    driver.find_element(By.CSS_SELECTOR, ".btn-group:nth-child(8) .filter-option").click()
                    sleep(3)
                    driver.find_element(By.LINK_TEXT, user['district']).click()

                    driver.find_element_by_id('DQJZDZ').send_keys(user['address'])

                    driver.find_element_by_id('DRTW').send_keys(user['temperature'])
               

                # promise = driver.find_element_by_name("GRCN_group")
                # promise.click()


                driver.switch_to.parent_frame()
                commit = driver.find_element_by_id('commit')
                commit.click()
                save_screenshot(driver,user)
            except Exception as e:
                writelog(f"===== ClockingIn Error Begin @ {datetime.now()} =====")
                writelog(f"Error occurred while clocking in ,retrying cnt = {i}, User = {user['username']}.\nStack Trace:{traceback.format_exc()}\n")
                writelog(f"===== ClockingIn Error End  @ {datetime.now()}  =====")
            else:
                if logSucceededRecord:writelog(f"Clocked in , user {user['username']} , time {datetime.now()}\n")
                break
            finally:
                sleep(5)
                driver.quit()
    log.close()