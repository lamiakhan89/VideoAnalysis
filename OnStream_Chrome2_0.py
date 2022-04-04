import os
import pytest
import subprocess
import shutil
import platform
import time
from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException, ElementClickInterceptedException, ElementNotInteractableException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.keys import Keys
from datetime import datetime, timedelta
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from conftest import all_ld, active_service
from UI_Constant import *
import UI_Constant
import logging
import json
logging.basicConfig(level=logging.DEBUG)
mylogger = logging.getLogger()
browser = os.path.basename(__file__).split("_")[1]
plat = platform.platform().split('-')
device = str(plat[0] + "-" + plat[1])

@pytest.fixture(scope="session", autouse=True)
def client_setup(influxdb_url,influxdb_token,influxdb_username,influxdb_password,influxdb_org):
         client = InfluxDBClient(url=influxdb_url,token=influxdb_token, username=influxdb_username,password=influxdb_password, org=influxdb_org)
         write_api = client.write_api(write_options=SYNCHRONOUS)
         return write_api

@pytest.fixture(scope="session", autouse=True)
def auto_start(request, onstream_version, onstream_url,client_setup,influxdb_bucket,influxdb_org,run):
    try:

        archive_version = os.path.abspath(os.curdir) + os.sep + 'Archived' + os.sep + onstream_version
        os.mkdir(archive_version)
    except FileNotFoundError:
        trd = os.path.abspath(os.curdir) + os.sep + 'Archived'
        os.mkdir(trd)
    except FileExistsError:
        pass

    count = 0
    for i in os.listdir(os.path.abspath(os.curdir) + os.sep + 'Archived' + os.sep + onstream_version):
        if not i.startswith('.'):
            count += 1

    testrun = count + 1
    try:
        archive = os.path.abspath(os.curdir) + os.sep + 'Archived' + os.sep + onstream_version + os.sep + str(browser) + '_' + str(testrun)
        os.mkdir(archive)
    except FileNotFoundError:
        at = os.path.abspath(os.curdir) + os.sep + 'Archived' + os.sep + onstream_version
        os.mkdir(at)
    except FileExistsError:
        pass
    test_start = [
        {
            "measurement": "OnStream",
            "tags": {
                "Software": onstream_version,
                "Test": run,
                "URL": onstream_url,
                "Browser": "Chrome",
                "Device": device,
            },
            "time": time.time_ns(),
            "fields": {
                "events_title": "test start",
                "text": "This is the start of test " + "1" + " on firmware " + onstream_version + " tested on " + onstream_url,
                "tags": "Onstream" + "," + "Chrome" + "," + "1" + "," + onstream_version + "," + onstream_url
            }
        }
    ]
    client_setup.write(bucket=influxdb_bucket,org=influxdb_org,record=test_start)

    def auto_fin():
        test_end = [
            {
                "measurement": "OnStream",
                "tags": {
                    "Software": onstream_version,
                    "Test": run,
                    "URL": onstream_url,
                    "Browser": "Chrome",
                    "Device": device,
                },
                "time": time.time_ns(),
                "fields": {
                    "events_title": "test end",
                    "text": "This is the end of test " + "1" + " on firmware " + onstream_version + " tested on " + onstream_url,
                    "tags": "Onstream" + "," + "Chrome" + "," + "1" + "," + onstream_version + "," + onstream_url
                }
            }
        ]
        client_setup.write(bucket=influxdb_bucket, org=influxdb_org, record=test_end)

        Pictures = os.path.abspath(os.curdir) + os.sep + 'Pictures' + os.sep
        Duration = os.path.abspath(os.curdir) + os.sep + 'Pictures' + os.sep

        dest = os.path.abspath(os.curdir) + os.sep + 'Archived' + os.sep + onstream_version + os.sep + str(browser) + '_' + str(testrun)

        try:
            PicturesFile = os.listdir(Pictures)
            for f in PicturesFile:
                if not f.startswith('.'):
                    shutil.move(Pictures + f, dest)
        except FileNotFoundError:
            print("File Not Found at " + Pictures)
            pass

        try:
            DurationFile = os.listdir(Duration)
            for f in DurationFile:
                if not f.startswith('.'):
                    shutil.move(Duration + f, dest)
        except FileNotFoundError:
            print("File Not Found at " + Duration)
            pass
        subprocess.run(['python3', 'ClearFolders.py'])

    request.addfinalizer(auto_fin)


@pytest.fixture(scope="class")
def directory(request):
    name = os.environ.get('PYTEST_CURRENT_TEST')
    direct = os.path.abspath(os.curdir) + os.sep + 'Pictures' + os.sep
    request.cls.direct = direct
    request.cls.name = name
    yield


@pytest.fixture(scope="class")
def setup(request, onstream_url, custom_logo):
    options = Options()
    options.add_argument('--no-sandbox')
    options.add_argument('--start-maximized')
    options.add_argument('--disable-extensions')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--ignore-certificate-errors')
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    dishtv = onstream_url
    driver.get(dishtv)
    logo = custom_logo  # Big logo on home screen
    src = driver.page_source
    request.cls.driver = driver
    request.cls.src = src
    request.cls.dishtv = dishtv
    mylogger.info(driver.get_window_size())
    driver.fullscreen_window()
    request.cls.logo = logo
    yield
    driver.quit()



@pytest.fixture(scope="class")
def current_time(request):
    t1 = datetime.now() + timedelta(hours=1)
    t2 = datetime.now() + timedelta(hours=2)
    t3 = datetime.now() + timedelta(hours=3)
    t4 = datetime.now() + timedelta(hours=4)

    if datetime.now().strftime('%M') < str(30):
        m = str("{0:0>2}".format(0))
    elif datetime.now().strftime('%M') >= str(30):
        m = str(30)
    now = datetime.now().strftime('%-I:' + m)
    now1 = t1.strftime('%-I:' + m)
    now2 = t2.strftime('%-I:' + m)
    now3 = t3.strftime('%-I:' + m)
    now4 = t4.strftime('%-I:' + m)
    request.cls.now = now
    request.cls.now1 = now1
    request.cls.now2 = now2
    request.cls.now3 = now3
    request.cls.now4 = now4
    yield


@pytest.mark.usefixtures("setup", "directory")
class TestVersion:
    def test_app_version(self, onstream_version, onstream_url,influxdb_bucket,influxdb_org,client_setup,run):
        try:
            WebDriverWait(self.driver, 200).until(ec.presence_of_element_located((By.XPATH, UI_Constant.home_button)))  # Wait for the Home Page to Load fully
            time.sleep(5)
            self.driver.find_element(By.XPATH,'//*[@id="HEADER_CONTAINER"]/div[2]/nav/div/button[5]').click()  # settings
            time.sleep(3)
            self.driver.find_element(By.XPATH,'//*[@id="LEGAL"]').click()  # legal
            time.sleep(5)
            v = self.driver.find_element(By.XPATH, '//*[@class="_2hnwQ2hn8tcdObPRmB_t2G"]')  # Find the Application Version text
            v = v.text.split('\n')[1].strip()
            mylogger.info(v)
            assert onstream_version == v


        except NoSuchElementException:
            self.driver.save_screenshot(self.direct + self.name + ".png")
            body = [
                {
                    "measurement": "OnStream",
                    "tags": {
                        "Software": onstream_version,
                        "Test": run,
                        "Pytest": self.name,
                        "URL": onstream_url,
                        "Browser": "Chrome",
                        "Device": device,
                    },
                    "time": time.time_ns(),
                    "fields": {
                        "element_not_found": 1,
                    }
                }
            ]
            client_setup.write(bucket=influxdb_bucket, org=influxdb_org, record=body)
            assert False, "Element was not found"
        except TimeoutException:
            self.driver.save_screenshot(self.direct + self.name + ".png")
            loading_circle = self.driver.find_elements(By.XPATH,
                                                       '//div[@class="nvI2gN1AMYiKwYvKEdfIc schema_accent_border-bottom schema_accent_border-right schema_accent_border-left"]')
            no_streaming = self.driver.find_elements(By.XPATH,
                                                     '//h1[contains(text(), "It appears that you are not able to connect to Streaming Services at this time.")]')
            error_404 = self.driver.find_elements(By.XPATH, '//h1[contains(text(), "Oops! Error 404")]')
            loading_element = self.driver.find_elements(By.XPATH, '//span[contains(text(), "Loading...")]')
            went_wrong = self.driver.find_elements(By.XPATH,
                                                   '//h2[contains(text(), "Something went wrong with the stream.")]')

            if len(loading_circle) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": run,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Chrome",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "loading_circle": 1,
                        }
                    }
                ]
                client_setup.write(bucket=influxdb_bucket, org=influxdb_org, record=body)
                assert False, "Stuck on loading screen"
            elif len(no_streaming) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": run,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Chrome",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "unable_to_connect": 1,
                        }
                    }
                ]
                client_setup.write(bucket=influxdb_bucket, org=influxdb_org, record=body)
                assert False, "It appears that you are not able to connect to Streaming Services at this time."
            elif len(error_404) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": run,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Chrome",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "error_404": 1,
                        }
                    }
                ]
                client_setup.write(bucket=influxdb_bucket, org=influxdb_org, record=body)
                assert False, "404 error"
            elif len(loading_element):
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": run,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Chrome",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "element_loading": 1,
                        }
                    }
                ]
                client_setup.write(bucket=influxdb_bucket, org=influxdb_org, record=body)
                assert False, "Stuck loading an element"
            elif len(went_wrong):
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": run,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Chrome",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "went_wrong": run,
                        }
                    }
                ]
                client_setup.write(bucket=influxdb_bucket, org=influxdb_org, record=body)
                assert False, "Something went wrong"
            else:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": run,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Chrome",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "timeout_exception": 1,
                        }
                    }
                ]
                client_setup.write(bucket=influxdb_bucket, org=influxdb_org, record=body)
                assert False, "timeout error"


@pytest.mark.usefixtures("setup", "directory")
class TestHomeScreen:
    def test_hero_screen(self, onstream_version, onstream_url,influxdb_bucket,influxdb_org,client_setup):
        try:
            WebDriverWait(self.driver, 60).until(ec.presence_of_element_located((By.XPATH, UI_Constant.home_button)))  # Wait for the Home Page to Load
            time.sleep(5)
            WebDriverWait(self.driver, 60).until(ec.presence_of_element_located((By.XPATH, '//*[@id="HERO_CAROUSEL_CONTAINER"]/div/ul/li[1]/button'))).click()  # 1st button click
            time.sleep(3)
            self.driver.find_element(By.XPATH,'//*[@id="HERO_CAROUSEL_CONTAINER"]/div/ul/li[2]/button').click()  # Second button click
            time.sleep(3)
            WebDriverWait(self.driver, 60).until(ec.presence_of_element_located( (By.XPATH, '//*[@id="HERO_CAROUSEL_CONTAINER"]/div/ul/li[1]/button'))).click()  # 1st  button click
            time.sleep(3)
            WebDriverWait(self.driver, 60).until(ec.presence_of_element_located((By.XPATH, '//*[@id="HERO_CAROUSEL_CONTAINER"]/div/div/div/div[2]/div/div/div/div/div/div/button'))).click()  # learn more
            time.sleep(5)
            self.driver.find_element(By.XPATH, '//*[@id="root"]/div[5]/div/div[1]/img').click()  # close button
            self.driver.find_element(By.XPATH,'//*[@id="HERO_CAROUSEL_CONTAINER"]/div/ul/li[2]/button').click()  # Second button click
            time.sleep(3)
            WebDriverWait(self.driver, 60).until(ec.presence_of_element_located((By.XPATH, '//*[@id="HERO_CAROUSEL_CONTAINER"]/div/div/div/div[3]/div/div/div/div/div/div/button'))).click()  # learn more
            time.sleep(2)
            self.driver.find_element(By.XPATH, '//*[@id="root"]/div[5]/div/div[1]/img').click()  # close button
            time.sleep(2)
            self.driver.find_element(By.XPATH,'//*[@id="HEADER_CONTAINER"]/div[1]/img').is_displayed()  #onstream  logo is displayed
            self.driver.find_element(By.XPATH, '//*[@id="HERO_CAROUSEL_CONTAINER"]/div/div/div/div[2]/div/div/div/div/div/div/div/div[2]/div[1]').is_displayed()  # second line of text
            self.driver.find_element(By.XPATH,'//*[@id="HERO_CAROUSEL_CONTAINER"]/div/div/div/div[2]/div/div/div/div/div/div/div/div[2]/div[1]').is_displayed()  # hero screen description



        except NoSuchElementException:
            self.driver.save_screenshot(self.direct + self.name + ".png")
            body = [
                {
                    "measurement": "OnStream",
                    "tags": {
                        "Software": onstream_version,
                        "Test": 1,
                        "Pytest": self.name,
                        "URL": onstream_url,
                        "Browser": "Chrome",
                        "Device": device,
                    },
                    "time": time.time_ns(),
                    "fields": {
                        "element_not_found": 1,
                    }
                }
            ]
            client_setup.write(bucket=influxdb_bucket, org=influxdb_org, record=body)
            assert False,"Element was not found"
        except TimeoutException:
            self.driver.save_screenshot(self.direct + self.name + ".png")
            loading_circle = self.driver.find_elements(By.XPATH,
                                                       '//div[@class="nvI2gN1AMYiKwYvKEdfIc schema_accent_border-bottom schema_accent_border-right schema_accent_border-left"]')
            no_streaming = self.driver.find_elements(By.XPATH,
                                                     '//h1[contains(text(), "It appears that you are not able to connect to Streaming Services at this time.")]')
            error_404 = self.driver.find_elements(By.XPATH, '//h1[contains(text(), "Oops! Error 404")]')
            loading_element = self.driver.find_elements(By.XPATH, '//span[contains(text(), "Loading...")]')
            went_wrong = self.driver.find_elements(By.XPATH,
                                                   '//h2[contains(text(), "Something went wrong with the stream.")]')
            if len(loading_circle) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Chrome",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "loading_circle": 1,
                        }
                    }
                ]
                client_setup.write(bucket=influxdb_bucket, org=influxdb_org, record=body)
                assert False, "Stuck on loading screen"
            elif len(no_streaming) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Chrome",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "unable_to_connect": 1,
                        }
                    }
                ]
                client_setup.write(bucket=influxdb_bucket, org=influxdb_org, record=body)
                assert False, "It appears that you are not able to connect to Streaming Services at this time."
            elif len(error_404) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Chrome",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "error_404": 1,
                        }
                    }
                ]
                client_setup.write(bucket=influxdb_bucket, org=influxdb_org, record=body)
                assert False, "404 error"
            elif len(loading_element):
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Chrome",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "element_loading": 1,
                        }
                    }
                ]
                client_setup.write(bucket=influxdb_bucket, org=influxdb_org, record=body)
                assert False, "Stuck loading an element"
            elif len(went_wrong):
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Chrome",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "went_wrong": 1,
                        }
                    }
                ]
                client_setup.write(bucket=influxdb_bucket, org=influxdb_org, record=body)
                assert False, "Something went wrong"
            else:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Chrome",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "timeout_exception": 1,
                        }
                    }
                ]
                client_setup.write(bucket=influxdb_bucket, org=influxdb_org, record=body)
                assert False, "timeout error"

    def test_featured_channels(self, onstream_version, onstream_url,influxdb_bucket,influxdb_org,client_setup ):
        try:
            WebDriverWait(self.driver, 60).until(ec.presence_of_element_located((By.XPATH, UI_Constant.home_button)))  # Wait for the Home Page to Load
            self.driver.fullscreen_window()
            time.sleep(3)
            ##fcd = self.driver.find_element(By.XPATH, '//*[@id="ITEM_SWIMLANE_INNER_CONTAINER_1_0"]/div')
            ##time.sleep(3)
            ##self.driver.execute_script('arguments[0].scrollIntoView(true);', fcd)  # Scroll Down to the Bottom
            ##time.sleep(5)
            WebDriverWait(self.driver, 60).until(ec.presence_of_element_located((By.XPATH, '//*[@id="root"]/div[1]/div/div[1]/div[2]/div/div/div/div[2]/div[1]/div[2]/div[2]/div/div/div[1]/div/div/div/div/div/div[3]/div[3]/h3'))).click()  # 1st box
            time.sleep(2)
            WebDriverWait(self.driver, 60).until(ec.presence_of_element_located((By.XPATH, '/html/body/div[5]/div[3]/div/div/div/div[3]/button'))).click()  # watch now
            time.sleep(2)
            WebDriverWait(self.driver, 60).until(ec.presence_of_element_located((By.XPATH, '//*[@id="dish-bitmovin-player"]/div[3]/div/div[1]/div[3]'))).click()  # click space
            time.sleep(2)
            self.driver.find_element(By.XPATH,'//*[@id="dish-bitmovin-player"]/div[3]/div/div[2]/div[3]/button').click()  # mini guide
            time.sleep(2)
            self.driver.find_element(By.XPATH, '//*[@id="dish-bitmovin-player"]/div[4]/div/div[4]/img').click()  # down
            time.sleep(2)
            self.driver.find_element(By.XPATH, '//*[@id="dish-bitmovin-player"]/div[4]/div/div[2]/img').click()  # up
            time.sleep(2)
            self.driver.find_element(By.XPATH, '//*[@id="dish-bitmovin-player"]/div[4]/div/div[4]/img').click()  # right
            time.sleep(2)
            self.driver.find_element(By.XPATH, '//*[@id="dish-bitmovin-player"]/div[4]/div/div[1]/img').click()  # left
            self.driver.find_element(By.XPATH, '//*[@id="WATCH_NOW_BUTTON"]/img').click()  # play video on one of the channels
            time.sleep(2)
            WebDriverWait(self.driver, 60).until(ec.presence_of_element_located((By.XPATH,'//*[@id="dish-bitmovin-player"]/div[3]/div/div[2]/div[1]/button'))).click()  # volume bar
            time.sleep(2)
            WebDriverWait(self.driver, 60).until(ec.presence_of_element_located((By.XPATH, '//*[@id="dish-bitmovin-player"]/div[3]/div/div[2]/div[2]/button'))).click()  # caption click
            WebDriverWait(self.driver, 60).until(ec.presence_of_element_located((By.XPATH, '//*[@id="subtitle-popper"]/ul/div[3]'))).click()  # english
            time.sleep(5)
            self.driver.find_element(By.XPATH, '//*[@id="PLAYER_CLOSE_BTN"]/img').click()  # close button
            time.sleep(5)
            self.driver.find_element(By.XPATH, '//*[@id="HEADER_CONTAINER"]/div[2]/nav/div/button[1]').click()  # home button
            time.sleep(5)
            self.driver.find_element(By.XPATH, '//*[@id="root"]/div[1]/div/div[1]/div[2]/div/div/div/div[2]/div[1]/div[2]/div[2]/div/div/div[3]/div/div/div/div/div/div[3]/div[3]/h3').click()  # play third video space
            time.sleep(4)
            self.driver.find_element(By.XPATH, '/html/body/div[5]/div[3]/div/div/div/div[3]/button').click()  # watch now
            time.sleep(20)
            self.driver.find_element(By.XPATH, '//*[@id="PLAYER_CLOSE_BTN"]/img').click()  # close button
            time.sleep(4)
            self.driver.find_element(By.XPATH,
                                     '//*[@id="root"]/div[1]/div/div[1]/div[2]/div/div/div/div[2]/h2[1]').is_displayed()  # featured channels wording showing
            self.driver.find_element(By.XPATH,
                                     '//*[@id="ITEM_SWIMLANE_INNER_CONTAINER_0_0"]/div/div[1]').is_displayed()  # square box
            self.driver.find_element(By.XPATH,
                                     '// *[@ id = "ITEM_SWIMLANE_INNER_CONTAINER_0_0"] / div / div[1]').is_displayed()  # box background image
            self.driver.find_element(By.XPATH,
                                     '//*[@id="ITEM_SWIMLANE_INNER_CONTAINER_0_0"]/div/div[3]/div[2]/img').is_displayed()  # check logo on each box
            self.driver.find_element(By.XPATH,'//*[@id="ITEM_SWIMLANE_INNER_CONTAINER_0_0"]/div/div[3]/div[3]/h3').is_displayed()  ## check title
            self.driver.find_element(By.XPATH,
                                     '//*[@id="ITEM_SWIMLANE_INNER_CONTAINER_0_0"]/div/div[3]/div[3]/h2[2]').is_displayed()  # check LIVE written and time remaining
            self.driver.find_element(By.XPATH,'//*[@id="ITEM_SWIMLANE_INNER_CONTAINER_0_1"]/div/div[2]/span').is_displayed()  # live button'''




          

        except NoSuchElementException:
            self.driver.save_screenshot(self.direct + self.name + ".png")
            body = [
                {
                    "measurement": "OnStream",
                    "tags": {
                        "Software": onstream_version,
                        "Test": 1,
                        "Pytest": self.name,
                        "URL": onstream_url,
                        "Browser": "Chrome",
                        "Device": device,
                    },
                    "time": time.time_ns(),
                    "fields": {
                        "element_not_found": 1,
                    }
                }
            ]
            client_setup.write(bucket=influxdb_bucket, org=influxdb_org, record=body)
            assert False, "Element was not found"
        except TimeoutException:
            self.driver.save_screenshot(self.direct + self.name + ".png")
            loading_circle = self.driver.find_elements(By.XPATH,
                                                       '//div[@class="nvI2gN1AMYiKwYvKEdfIc schema_accent_border-bottom schema_accent_border-right schema_accent_border-left"]')
            no_streaming = self.driver.find_elements(By.XPATH,
                                                     '//h1[contains(text(), "It appears that you are not able to connect to Streaming Services at this time.")]')
            error_404 = self.driver.find_elements(By.XPATH, '//h1[contains(text(), "Oops! Error 404")]')
            loading_element = self.driver.find_elements(By.XPATH, '//span[contains(text(), "Loading...")]')
            went_wrong = self.driver.find_elements(By.XPATH,
                                                   '//h2[contains(text(), "Something went wrong with the stream.")]')
            if len(loading_circle) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Chrome",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "loading_circle": 1,
                        }
                    }
                ]
                client_setup.write(bucket=influxdb_bucket, org=influxdb_org, record=body)
                assert False, "Stuck on loading screen"
            elif len(no_streaming) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Chrome",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "unable_to_connect": 1,
                        }
                    }
                ]
                client_setup.write(bucket=influxdb_bucket, org=influxdb_org, record=body)
                assert False, "It appears that you are not able to connect to Streaming Services at this time."
            elif len(error_404) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Chrome",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "error_404": 1,
                        }
                    }
                ]
                client_setup.write(bucket=influxdb_bucket, org=influxdb_org, record=body)
                assert False, "404 error"
            elif len(loading_element):
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Chrome",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "element_loading": 1,
                        }
                    }
                ]
                client_setup.write(bucket=influxdb_bucket, org=influxdb_org, record=body)
                assert False, "Stuck loading an element"
            elif len(went_wrong):
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Chrome",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "went_wrong": 1,
                        }
                    }
                ]
                client_setup.write(bucket=influxdb_bucket, org=influxdb_org, record=body)
                assert False, "Something went wrong"
            else:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Chrome",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "timeout_exception": 1,
                        }
                    }
                ]
                client_setup.write(bucket=influxdb_bucket, org=influxdb_org, record=body)
                assert False, "timeout error"

    def test_sports(self, onstream_version, onstream_url,influxdb_bucket,influxdb_org,client_setup):
        try:
            WebDriverWait(self.driver, 60).until(ec.presence_of_element_located((By.XPATH, UI_Constant.home_button)))  # Wait for the Home Page to Load
            time.sleep(5)
            spb = self.driver.find_element(By.XPATH, '//*[@id="root"]/div[1]/div/div[1]/div[2]/div/div/div/div[2]/div[2]/div[2]/div[2]/div/div/div/div/div/div/div/div/img')
            time.sleep(3)
            self.driver.execute_script('arguments[0].scrollIntoView(true);', spb)  # Scroll Down to the Bottom
            time.sleep(5)
            WebDriverWait(self.driver, 80).until(ec.presence_of_element_located((By.XPATH, '//*[@id="root"]/div[1]/div/div[1]/div[2]/div/div/div/div[2]/div[2]/div[2]/div[2]/div/div/div/div/div/div/div/div/img'))).click()  #sportsclick
            self.driver.set_window_size(1700,971)
            time.sleep(15)
            self.driver.find_element(By.XPATH, '//*[@id="root"]/div[1]/div/div[1]/div[2]/div/div/div/div/div[2]/div[2]/div[1]/button').click()  # nba right arrow
            time.sleep(2)
            self.driver.find_element(By.XPATH,'//*[@id="root"]/div[1]/div/div[1]/div[2]/div/div/div/div/div[2]/div[2]/div[1]/button[1]').click()  # nba left arrow
            time.sleep(2)
            self.driver.find_element(By.XPATH,'//*[@id="root"]/div[1]/div/div[1]/div[2]/div/div/div/div/div[2]/div[2]/div[2]/div/div/div[1]/div/div/div/div/div').click()  # NBA Click
            time.sleep(5)
            self.driver.find_element(By.XPATH, '/html/body/div[5]/div[3]/div/div[1]/button').click()  # x arrow
            time.sleep(5)
            self.driver.find_element(By.XPATH, '//*[@id="root"]/div[1]/div/div[1]/div[2]/div/div/div/div/div[1]/div[2]/div[2]/div/div/div/div/div/div/div/div').click()  # nfl
            time.sleep(5)
            self.driver.find_element(By.XPATH,'/html/body/div[5]/div[3]/div/div[1]/button').click()  # x nfl
            time.sleep(10)
            nhl = self.driver.find_element(By.XPATH, '//*[@id="root"]/div[1]/div/div[1]/div[2]/div/div/div/div/div[3]/div[2]/div[2]/div/div/div[1]')
            self.driver.execute_script('arguments[0].scrollIntoView(true);', nhl)  # Scroll Down to the Bottom
            time.sleep(10)
            self.driver.find_element(By.XPATH, '//*[@id="root"]/div[1]/div/div[1]/div[2]/div/div/div/div/div[3]/div[2]/div[2]/div/div/div[1]').click()  # nhl click
            time.sleep(5)
            self.driver.find_element(By.XPATH, '/html/body/div[5]/div[3]/div/div[1]/button').click()  # x nhl
            self.driver.find_element(By.XPATH, '//*[@id="root"]/div[1]/div/div[1]/div[2]/div/div/div/div/div[3]/div[2]/div[1]/button').click()  # nhl  right arrow
            time.sleep(2)
            self.driver.find_element(By.XPATH, '//*[@id="root"]/div[1]/div/div[1]/div[2]/div/div/div/div/div[3]/div[2]/div[1]/button[1]').click()  #nhl  left arrow
            time.sleep(4)
            self.driver.find_element(By.XPATH, '//*[@id="HEADER_CONTAINER"]/div[2]/nav/div/button[1]').click()  # x homepage click
            time.sleep(5)
            self.driver.find_element(By.XPATH,
                                     '//*[@id="root"]/div/div/div[1]/div[2]/div/div[2]/div[2]/div[2]/div/div[1]/div/div/div[1]/div[1]/div/div ').is_displayed()  # Words communitity an remove this
            self.driver.find_element(By.XPATH,
                                     '//*[@id="root"]/div/div/div[1]/div[2]/div/div[1]/div[2]/div[2]/div/div[1]/div/div/div[1]/div[1]/div/div (large main issue) ').is_displayed()  # Words community information shown
            self.driver.find_element(By.XPATH,
                                     '//*[@id="root"]/div[1]/div/div[1]/div[2]/div/div/div/div[2]/h2[2]').is_displayed()  # Words sports
            self.driver.find_element(By.XPATH,
                                     '//*[@id="ITEM_SWIMLANE_INNER_CONTAINER_1_0"]/div').is_displayed()  # square box
            self.driver.find_element(By.XPATH,
                                     '//*[@id="ITEM_SWIMLANE_INNER_CONTAINER_1_0"]/div/div[1]').is_displayed()  # box background image
            self.driver.find_element(By.XPATH,
                                     '//*[@id="ITEM_SWIMLANE_INNER_CONTAINER_1_0"]/div/img').is_displayed()  ## football image'''






        except NoSuchElementException:
            self.driver.save_screenshot(self.direct + self.name + ".png")
            body = [
                {
                    "measurement": "OnStream",
                    "tags": {
                        "Software": onstream_version,
                        "Test": 1,
                        "Pytest": self.name,
                        "URL": onstream_url,
                        "Browser": "Chrome",
                        "Device": device,
                    },
                    "time": time.time_ns(),
                    "fields": {
                        "element_not_found": 1,
                    }
                }
            ]
            client_setup.write(bucket=influxdb_bucket, org=influxdb_org, record=body)
            assert False, "Element was not found"
        except TimeoutException:
            self.driver.save_screenshot(self.direct + self.name + ".png")
            loading_circle = self.driver.find_elements(By.XPATH,
                                                       '//div[@class="nvI2gN1AMYiKwYvKEdfIc schema_accent_border-bottom schema_accent_border-right schema_accent_border-left"]')
            no_streaming = self.driver.find_elements(By.XPATH,
                                                     '//h1[contains(text(), "It appears that you are not able to connect to Streaming Services at this time.")]')
            error_404 = self.driver.find_elements(By.XPATH, '//h1[contains(text(), "Oops! Error 404")]')
            loading_element = self.driver.find_elements(By.XPATH, '//span[contains(text(), "Loading...")]')
            went_wrong = self.driver.find_elements(By.XPATH,
                                                   '//h2[contains(text(), "Something went wrong with the stream.")]')
            if len(loading_circle) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Chrome",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "loading_circle": 1,
                        }
                    }
                ]
                client_setup.write(bucket=influxdb_bucket, org=influxdb_org, record=body)
                assert False, "Stuck on loading screen"
            elif len(no_streaming) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Chrome",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "unable_to_connect": 1,
                        }
                    }
                ]
                client_setup.write(bucket=influxdb_bucket, org=influxdb_org, record=body)
                assert False, "It appears that you are not able to connect to Streaming Services at this time."
            elif len(error_404) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Chrome",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "error_404": 1,
                        }
                    }
                ]
                client_setup.write(bucket=influxdb_bucket, org=influxdb_org, record=body)
                assert False, "404 error"
            elif len(loading_element):
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Chrome",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {

                            "element_loading": 1,
                        }
                    }
                ]
                client_setup.write(bucket=influxdb_bucket, org=influxdb_org, record=body)
                assert False, "Stuck loading an element"
            elif len(went_wrong):
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Chrome",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "went_wrong": 1,
                        }
                    }
                ]
                client_setup.write(bucket=influxdb_bucket, org=influxdb_org, record=body)
                assert False, "Something went wrong"
            else:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Chrome",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "timeout_exception": 1,
                        }
                    }
                ]
                client_setup.write(bucket=influxdb_bucket, org=influxdb_org, record=body)
                assert False, "timeout error"

@pytest.mark.usefixtures("setup", "directory")
class TestGuide:
    def test_modern_guide(self, onstream_version, onstream_url,influxdb_bucket,influxdb_org,client_setup):
        try:
            WebDriverWait(self.driver, 60).until(ec.presence_of_element_located((By.XPATH, UI_Constant.home_button)))
            time.sleep(3)
            self.driver.find_element(By.XPATH,'//*[@id="HEADER_CONTAINER"]/div[2]/nav/div/button[5]').click()  # settings new
            time.sleep(3)
            WebDriverWait(self.driver, 60).until(ec.presence_of_element_located((By.XPATH, UI_Constant.guide_choice))).click() #change guide style
            time.sleep(3)
            WebDriverWait(self.driver, 60).until( ec.presence_of_element_located((By.XPATH, UI_Constant.modern_guide))).click() #modern guide
            time.sleep(3)
            WebDriverWait(self.driver, 60).until(ec.presence_of_element_located((By.XPATH, UI_Constant.tv_guide))).click()  # tv guide
            time.sleep(2)
            self.driver.find_element(By.XPATH, '//*[@id="root"]/div[1]/div/div[1]/div[2]/div/div[1]/div[2]/div[3]/img').click()  # channel right arrow
            time.sleep(2)
            self.driver.find_element(By.XPATH, '//*[@id="root"]/div[1]/div/div[1]/div[2]/div/div[1]/div[2]/div[1]/img').click()  # channel left arrow
            time.sleep(3)
            play_buttons = self.driver.find_elements(By.XPATH,'//*[@class="_1TjpZPuLnjCBGtAtPLv7bb"]') #play video
            mylogger.info(play_buttons)
            time.sleep(3)

            for i in range(len(play_buttons)):
                try:
                    WebDriverWait(self.driver, 60).until(ec.visibility_of_element_located( (By.XPATH,'//*[@id="root"]/div/div/div[1]/div[2]/div/div[1]/div[1]' )))  # wait for the guide to populate
                    self.driver.find_elements(By.XPATH,'//*[@class="_1TjpZPuLnjCBGtAtPLv7bb"]')[i].click()
                    time.sleep(3)
                    WebDriverWait(self.driver, 60).until(ec.presence_of_element_located( (By.XPATH, '//*[@id="dish-bitmovin-player"]/div[3]/div'))).click()  # click space
                    time.sleep(2)
                    self.driver.find_element(By.XPATH, '//*[@id="dish-bitmovin-player"]/div[3]/div/div[2]/div[1]/button/img').click()  # Click volume button
                    time.sleep(3)
                    close = self.driver.find_element(By.XPATH, '//*[@id="PLAYER_CLOSE_BTN"]/img')  # close video
                    time.sleep(3)
                    actions = ActionChains(self.driver)
                    actions.move_to_element(close).click().perform()
                    time.sleep(3)
                except:
                    mylogger.error("failed channel number {}".format(i))
            self.driver.find_element(By.XPATH,
                                     '//*[@id="root"]/div/div/div[1]/div[2]/div/div[1]/div[2]/div[2]/div/div[1]/div/div/div[2]/div/span[1]').is_displayed()  # title
            self.driver.find_element(By.XPATH,
                                     '//*[@id="root"]/div/div/div[1]/div[2]/div/div[1]/div[2]/div[2]/div/div[1]/div/div/div[2]/div/span[1]').is_displayed()  # description
            self.driver.find_element(By.XPATH,
                                     '//*[@id="root"]/div/div/div[1]/div[2]/div/div[1]/div[2]/div[2]/div/div[1]/div/div/div[2]/span').is_displayed()  # time and time left
            self.driver.find_element(By.XPATH,
                                     '//*[@id="root"]/div/div/div[1]/div[2]/div/div[1]/div[2]/div[2]/div/div[1]/div/div/div[1]/img').is_displayed()  # image
            self.driver.find_element(By.XPATH,
                                     '//*[@id="root"]/div/div/div[1]/div[2]/div/div[1]/div[2]/div[2]/div/div[1]/div/div/div[1]').is_displayed()  #box
            self.driver.find_element(By.XPATH,
                                     '//*[@id="root"]/div/div/div[1]/div[2]/div/div[1]').is_displayed()  # 1 inch of space inbetween next show
            self.driver.find_element(By.XPATH, '//*[@id="root"]/div/div/div[1]/div[2]/div/div[1]/div[1]').is_displayed()  # logo

        except NoSuchElementException:
            self.driver.save_screenshot(self.direct + self.name + ".png")
            body = [
                {
                    "measurement": "OnStream",
                    "tags": {
                        "Software": onstream_version,
                        "Test": 1,
                        "Pytest": self.name,
                        "URL": onstream_url,
                        "Browser": "Chrome",
                        "Device": device,
                    },
                    "time": time.time_ns(),
                    "fields": {
                        "element_not_found": 1,
                    }
                }
            ]
            client_setup.write(bucket=influxdb_bucket, org=influxdb_org, record=body)
            assert False, "Element was not found" # element not reachable can not reach it
        except TimeoutException:
            self.driver.save_screenshot(self.direct + self.name + ".png")
            loading_circle = self.driver.find_elements(By.XPATH,'//div[@class="nvI2gN1AMYiKwYvKEdfIc schema_accent_border-bottom schema_accent_border-right schema_accent_border-left"]')
            no_streaming = self.driver.find_elements(By.XPATH,
                                                     '//h1[contains(text(), "It appears that you are not able to connect to Streaming Services at this time.")]')
            error_404 = self.driver.find_elements(By.XPATH, '//h1[contains(text(), "Oops! Error 404")]')
            loading_element = self.driver.find_elements(By.XPATH, '//span[contains(text(), "Loading...")]')
            went_wrong = self.driver.find_elements(By.XPATH,
                                                   '//h2[contains(text(), "Something went wrong with the stream.")]')
            if len(loading_circle) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Chrome",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "loading_circle": 1,
                        }
                    }
                ]
                client_setup.write(bucket=influxdb_bucket, org=influxdb_org, record=body)
                assert False, "Stuck on loading screen"
            elif len(no_streaming) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Chrome",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "unable_to_connect": 1,
                        }
                    }
                ]
                client_setup.write(bucket=influxdb_bucket, org=influxdb_org, record=body)
                assert False, "It appears that you are not able to connect to Streaming Services at this time."
            elif len(error_404) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Chrome",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "error_404": 1,
                        }
                    }
                ]
                client_setup.write(bucket=influxdb_bucket, org=influxdb_org, record=body)
                assert False, "404 error"
            elif len(loading_element):
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Chrome",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "element_loading": 1,
                        }
                    }
                ]
                #.write_points(body)
                assert False, "Stuck loading an element"
            elif len(went_wrong):
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Chrome",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "went_wrong": 1,
                        }
                    }
                ]
                client_setup.write(bucket=influxdb_bucket, org=influxdb_org, record=body)
                assert False, "Something went wrong"
            else:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Chrome",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "timeout_exception": 1,
                        }
                    }
                ]
                client_setup.write(bucket=influxdb_bucket, org=influxdb_org, record=body)
                assert False, "timeout error"

    def test_classic_guide(self, onstream_version, onstream_url,influxdb_bucket,influxdb_org,client_setup ):
        try:
            WebDriverWait(self.driver, 60).until(ec.presence_of_element_located((By.XPATH, UI_Constant.home_button)))
            WebDriverWait(self.driver, 60).until(ec.presence_of_element_located((By.XPATH, UI_Constant.home_button)))
            time.sleep(3)
            self.driver.find_element(By.XPATH,'//*[@id="HEADER_CONTAINER"]/div[2]/nav/div/button[5]').click()  # settings new
            time.sleep(3)
            WebDriverWait(self.driver, 60).until(ec.presence_of_element_located((By.XPATH, UI_Constant.guide_choice))).click()  # change guide style
            time.sleep(3)
            WebDriverWait(self.driver, 60).until(ec.presence_of_element_located((By.XPATH, UI_Constant.classic_guide))).click()  #classic
            time.sleep(4)
            WebDriverWait(self.driver, 60).until(ec.presence_of_element_located((By.XPATH, UI_Constant.tv_guide))).click()  # tv guide
            time.sleep(2)
            play_buttons = self.driver.find_elements(By.XPATH, '//*[@class="MuiSvgIcon-root MuiSvgIcon-fontSizeMedium css-m9dfmo"]')  # play video
            mylogger.info(play_buttons)
            time.sleep(10)

            for i in range(len(play_buttons)): ## start loops
                try:
                    time.sleep(10)
                    WebDriverWait(self.driver, 60).until(ec.visibility_of_element_located((By.XPATH,'//*[@id="root"]/div/div/div[1]/div[2]/div/div[1]/div[1]')))  # wait for the guide to populate
                    self.driver.find_elements(By.XPATH, '//*[@class="MuiSvgIcon-root MuiSvgIcon-fontSizeMedium css-m9dfmo"]')[i].click()
                    time.sleep(3)  # for video time
                    WebDriverWait(self.driver, 60).until(ec.presence_of_element_located((By.XPATH, '//*[@id="dish-bitmovin-player"]/div[3]/div'))).click()  # click space
                    time.sleep(5)
                    self.driver.find_element(By.XPATH,'//*[@id="dish-bitmovin-player"]/div[3]/div/div[2]/div[1]/button/img').click()  # Click volume button
                    time.sleep(3)
                    close = self.driver.find_element(By.XPATH, '//*[@id="PLAYER_CLOSE_BTN"]/img')  # close video
                    time.sleep(3)
                    actions = ActionChains(self.driver)
                    actions.move_to_element(close).click().perform()
                    time.sleep(3)
                except:
                    mylogger.error("failed channel number {}".format(i))
                    WebDriverWait(self.driver, 60).until(ec.presence_of_element_located((By.XPATH, UI_Constant.tv_guide))).click()

        ##outside loop
            '''time.sleep(2)
            self.driver.find_element(By.XPATH,'//*[@id="HEADER_CONTAINER"]/div[2]/nav/div/button[3]').click()  # settings new
            time.sleep(3)
            self.driver.find_element(By.XPATH,'//*[@id="root"]/div[1]/div/div[1]/div[2]/div/div/div[2]/div/div/div[3]/button/div[2]/img').click()  # change guide style
            time.sleep(2)
            self.driver.find_element(By.XPATH,'//*[@id="root"]/div[1]/div/div[1]/div[2]/div/div/div[2]/div/div/div[3]/button[2]').click()  # classic
            time.sleep(2)
            self.driver.find_element(By.XPATH,'//*[@id="HEADER_CONTAINER"]/div[2]/nav/div/button[2]').click()  # tv guide
            time.sleep(5)
            play_buttons = self.driver.find_elements(By.XPATH, '//*[@class="MuiSvgIcon-root MuiSvgIcon-fontSizeMedium css-m9dfmo"]')  # play video
            mylogger.info("mytest.dish")
            mylogger.info(play_buttons)
            time.sleep(3)
            for i in range(len(play_buttons)):
                WebDriverWait(self.driver, 10).until(ec.visibility_of_element_located((By.XPATH,'//*[@id="root"]/div/div/div[1]/div[2]/div/div[1]/div[1]')))  # wait for the guide to populate
                self.driver.find_elements(By.XPATH, '//*[@class="MuiSvgIcon-root MuiSvgIcon-fontSizeMedium css-m9dfmo"]')[i].click()
                time.sleep(2)
                WebDriverWait(self.driver, 60).until(ec.presence_of_element_located((By.XPATH, '//*[@id="dish-bitmovin-player"]/div[3]/div/div[1]/div[3]'))).click()  # click space
                time.sleep(2)
                WebDriverWait(self.driver, 60).until(ec.presence_of_element_located((By.XPATH,'//*[@id="dish-bitmovin-player"]/div[3]/div/div[2]/div[1]/button'))).click()  # volume bar
                time.sleep(2)
                WebDriverWait(self.driver, 60).until(ec.presence_of_element_located((By.XPATH, '//*[@id="dish-bitmovin-player"]/div[3]/div/div[2]/div[2]/button'))).click()  # caption click
                WebDriverWait(self.driver, 60).until(ec.presence_of_element_located((By.XPATH, '//*[@id="subtitle-popper"]/ul/div[3]'))).click()  # english
                time.sleep(10)
                close = self.driver.find_element(By.XPATH, '//*[@id="PLAYER_CLOSE_BTN"]/img')  # close video
                time.sleep(3)
                actions = ActionChains(self.driver)
                actions.move_to_element(close).click().perform()
                time.sleep(3)
                close.click()

            self.driver.find_element(By.XPATH,'//*[@id="root"]/div/div/div[1]/div[2]/div/div/div/div/div/div[4]/div/div/div/div[1]').is_displayed()  # time
            self.driver.find_element(By.XPATH,'//*[@id="root"]/div/div/div[1]/div[2]/div/div/div/div/div/div[1]/div/div[2]/div/div/div[1]/div/div[1]/div/div/div[1]/div/div/div[2]/div[1]').is_displayed()  # title
            self.driver.find_element(By.XPATH,'//*[@id="root"]/div/div/div[1]/div[2]/div/div/div/div/div/div[1]/div/div[2]/div/div/div[1]/div/div[1]/div/div/div[1]/div/div/div[2]/div[2]').is_displayed()  # description
            self.driver.find_element(By.XPATH,'//*[@id="root"]/div/div/div[1]/div[2]/div/div/div/div/div/div[3]/div[2]/div/div[1]/div/img').is_displayed()  # logo'''




            logos = self.driver.find_elements(By.XPATH, '//*[@class="_3f53WAdXRRgvavG8gcvjRb"]')  # Channel Logos
            guide_uid = []
            guide_images = []
            for i in range(
                    len(logos)):  # A for loop that collects certain information from the OnStream guide which will be validated against the JSON information
                guide_uid.append(logos[i].get_attribute("alt"))
                guide_images.append(logos[i].get_attribute('src'))
            all_guide_uid = list(dict.fromkeys(guide_uid))
            all_guide_images = list(dict.fromkeys(guide_images))
            '''if len(logos) == len(active_service):
                assert True  # Number of Logos is the same as the number of channels
            else:
                assert False'''
            all_logos =[]
            for subdir, dirs, files in os.walk(os.path.abspath(
                    os.curdir + os.sep + 'logos' + os.sep)):  # A for loop which goes through the logos folder and collects the necessary data for future parsing
                files = [f for f in files if not f[0] == '.']
                dirs[:] = [d for d in dirs if not d[0] == '.']
                for file in files:
                    filepath = subdir + os.sep + file
                    all_logos.append(filepath)


            for js in all_logos:  # Take the JSON data from the above for loop and delete un-needed information and create a new list
                with open(js) as json_file:
                    ld = json.load(json_file)
                    del ld['is_hd']
                    del ld['service_type']
                    all_ld.append(ld)
            mylogger.info(all_guide_uid)
            for gu in all_guide_uid:  # A for loop which compares the list of JSON data with the list of Guide Data in OnStream
                for temp_id in all_ld:
                    if str(temp_id['suid']) in str(gu):
                        mylogger.info(temp_id)
                        mylogger.info(gu)
                        break
                break

        except NoSuchElementException:
            self.driver.save_screenshot(self.direct + self.name + ".png")
            body = [
                {
                    "measurement": "OnStream",
                    "tags": {
                        "Software": onstream_version,
                        "Test": 1,
                        "Pytest": self.name,
                        "URL": onstream_url,
                        "Browser": "Chrome",
                        "Device": device,
                    },
                    "time": time.time_ns(),
                    "fields": {
                        "element_not_found": 1,
                    }
                }
            ]
            client_setup.write(bucket=influxdb_bucket, org=influxdb_org, record=body)
            assert False, "Element was not found"
        except TimeoutException:
            self.driver.save_screenshot(self.direct + self.name + ".png")
            loading_circle = self.driver.find_elements(By.XPATH,
                                                       '//div[@class="nvI2gN1AMYiKwYvKEdfIc schema_accent_border-bottom schema_accent_border-right schema_accent_border-left"]')
            no_streaming = self.driver.find_elements(By.XPATH,
                                                     '//h1[contains(text(), "It appears that you are not able to connect to Streaming Services at this time.")]')
            error_404 = self.driver.find_elements(By.XPATH, '//h1[contains(text(), "Oops! Error 404")]')
            loading_element = self.driver.find_elements(By.XPATH, '//span[contains(text(), "Loading...")]')
            went_wrong = self.driver.find_elements(By.XPATH,
                                                   '//h2[contains(text(), "Something went wrong with the stream.")]')
            if len(loading_circle) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Chrome",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "loading_circle": 1,
                        }
                    }
                ]
                client_setup.write(bucket=influxdb_bucket, org=influxdb_org, record=body)
                assert False, "Stuck on loading screen"
            elif len(no_streaming) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Chrome",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "unable_to_connect": 1,
                        }
                    }
                ]
                client_setup.write(bucket=influxdb_bucket, org=influxdb_org, record=body)

                assert False, "It appears that you are not able to connect to Streaming Services at this time."
            elif len(error_404) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Chrome",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "error_404": 1,
                        }
                    }
                ]
                client_setup.write(bucket=influxdb_bucket, org=influxdb_org, record=body)

                assert False, "404 error"
            elif len(loading_element):
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Chrome",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "element_loading": 1,
                        }
                    }
                ]
                client_setup.write(bucket=influxdb_bucket, org=influxdb_org, record=body)

                assert False, "Stuck loading an element"
            elif len(went_wrong):
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Chrome",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "went_wrong": 1,
                        }
                    }
                ]
                client_setup.write(bucket=influxdb_bucket, org=influxdb_org, record=body)
                assert False, "Something went wrong"
            else:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Chrome",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "timeout_exception": 1,
                        }
                    }
                ]
                client_setup.write(bucket=influxdb_bucket, org=influxdb_org, record=body)
                assert False, "timeout error"




@pytest.mark.usefixtures("setup", "directory")
class TestDemand:
    def test_on_demand(self, onstream_version, onstream_url,influxdb_bucket,influxdb_org,client_setup ):
        try:
            WebDriverWait(self.driver, 60).until(ec.presence_of_element_located((By.XPATH, UI_Constant.home_button)))  # Wait for the Home Page to Load
            time.sleep(3)
            self.driver.find_element(By.XPATH,'//*[@id="HEADER_CONTAINER"]/div[2]/nav/div/button[3]').click()  # On demand button
            time.sleep(7)
            self.driver.find_element(By.XPATH, '//*[@id="root"]/div[1]/div/div[1]/div[2]/div/div/div[1]/div[2]/div[1]/button').click()  # right arow trending content
            time.sleep(7)
            self.driver.find_element(By.XPATH, '//*[@id="root"]/div[1]/div/div[1]/div[2]/div/div/div[1]/div[2]/div[1]/button').click()  # left arrow trending contenet
            time.sleep(7)
            self.driver.find_element(By.XPATH, '//*[@id="root"]/div[1]/div/div[1]/div[2]/div/div/div[1]/div[2]/div[2]/div/div/div[6]').click() #cobrakai
            time.sleep(15)
            self.driver.find_element(By.XPATH, '/html/body/div[5]/div[3]/div/div/div/div[3]/div[1]/button').click()  # play button
            time.sleep(5)
            self.driver.find_element(By.XPATH,'/html/body/div[6]/div[2]/div/div/button[1]').click()  # paramount
            time.sleep(4)
            self.driver.switch_to.window(self.driver.window_handles[0])  # Switch to previous tab
            time.sleep(5)
            self.driver.find_element(By.XPATH, '/html/body/div[6]/div[2]/div/button').click()  # x close
            time.sleep(3)
            self.driver.find_element(By.XPATH, '/html/body/div[5]/div[3]/div/button').click()  # x close
            time.sleep(4)
            self.driver.find_element(By.XPATH,'//*[@id="HEADER_CONTAINER"]/div[2]/nav/div/button[3]').click()  # On demand button
            time.sleep(4)
            self.driver.find_element(By.XPATH,'//*[@id="root"]/div[1]/div/div[1]/div[2]/div/div/div[2]/div[2]/div[1]/button').click()  # right button popular shows
            time.sleep(5)
            self.driver.find_element(By.XPATH,'//*[@id="root"]/div[1]/div/div[1]/div[2]/div/div/div[2]/div[2]/div[2]/div/div/div[10]/div/div/div/div/div').click()  # see all
            time.sleep(2)
            self.driver.find_element(By.XPATH,'//*[@id="root"]/div[1]/div/div[1]/div[2]/div/div/div[2]/div/div').click()  # hawkeye
            time.sleep(15)
            self.driver.find_element(By.XPATH,'/html/body/div[5]/div[3]/div/div/div/div[3]/div[1]/button').click()  # play button
            time.sleep(5)
            self.driver.find_element(By.XPATH, '/html/body/div[6]/div[2]/div/div/button').click()  # disney
            time.sleep(4)
            self.driver.switch_to.window(self.driver.window_handles[0])  # Switch to previous tab
            time.sleep(5)
            self.driver.find_element(By.XPATH, '/html/body/div[6]/div[2]/div/button').click()  # x close
            time.sleep(3)
            self.driver.find_element(By.XPATH, '/html/body/div[5]/div[3]/div/button').click()  # x close
            time.sleep(4)
            self.driver.find_element(By.XPATH, '//*[@id="HEADER_CONTAINER"]/div[2]/nav/div/button[3]').click()  # On demand button
            self.driver.find_element(By.XPATH,
                                     '//*[@id="root"]/div[1]/div/div[1]/div[2]/div/div/div[1]/div[1]/h3').is_displayed()  # trending content
            self.driver.find_element(By.XPATH,
                                     '//*[@id="root"]/div[1]/div/div[1]/div[2]/div/div/div[1]/div[2]/div[2]/div/div/div[6]/div/div/div/div/div').is_displayed()  # movie box



        except NoSuchElementException:
            self.driver.save_screenshot(self.direct + self.name + ".png")
            body = [
                {
                    "measurement": "OnStream",
                    "tags": {
                        "Software": onstream_version,
                        "Test": 1,
                        "Pytest": self.name,
                        "URL": onstream_url,
                        "Browser": "Chrome",
                        "Device": device,
                    },
                    "time": time.time_ns(),
                    "fields": {
                        "element_not_found": 1,
                    }
                }
            ]
            client_setup.write(bucket=influxdb_bucket, org=influxdb_org, record=body)
            assert False, "Element was not found"
        except TimeoutException:
            self.driver.save_screenshot(self.direct + self.name + ".png")
            loading_circle = self.driver.find_elements(By.XPATH,
                                                 '//div[@class="nvI2gN1AMYiKwYvKEdfIc schema_accent_border-bottom schema_accent_border-right schema_accent_border-left"]')
            no_streaming = self.driver.find_elements(By.XPATH,
                                                     '//h1[contains(text(), "It appears that you are not able to connect to Streaming Services at this time.")]')
            error_404 = self.driver.find_elements(By.XPATH, '//h1[contains(text(), "Oops! Error 404")]')
            loading_element = self.driver.find_elements(By.XPATH, '//span[contains(text(), "Loading...")]')
            went_wrong = self.driver.find_elements(By.XPATH,
                                                   '//h2[contains(text(), "Something went wrong with the stream.")]')
            if len(loading_circle) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Chrome",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "loading_circle": 1,
                        }
                    }
                ]
                client_setup.write(bucket=influxdb_bucket, org=influxdb_org, record=body)
                assert False, "Stuck on loading screen"
            elif len(no_streaming) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Chrome",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "unable_to_connect": 1,
                        }
                    }
                ]
                client_setup.write(bucket=influxdb_bucket, org=influxdb_org, record=body)
                assert False, "It appears that you are not able to connect to Streaming Services at this time."
            elif len(error_404) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Chrome",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "error_404": 1,
                        }
                    }
                ]
                client_setup.write(bucket=influxdb_bucket, org=influxdb_org, record=body)
                assert False, "404 error"
            elif len(loading_element):
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Chrome",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "element_loading": 1,
                        }
                    }
                ]
                client_setup.write(bucket=influxdb_bucket, org=influxdb_org, record=body)
                assert False, "Stuck loading an element"
            elif len(went_wrong):
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Chrome",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "went_wrong": 1,
                        }
                    }
                ]
                client_setup.write(bucket=influxdb_bucket, org=influxdb_org, record=body)
                assert False, "Something went wrong"
            else:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Chrome",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "timeout_exception": 1,
                        }
                    }
                ]
                client_setup.write(bucket=influxdb_bucket, org=influxdb_org, record=body)
                assert False, "timeout error"

@pytest.mark.usefixtures("setup", "directory")
class TestSearch:
    def test_search_button(self, onstream_version, onstream_url,influxdb_bucket,influxdb_org,client_setup ):
            try:
                WebDriverWait(self.driver, 60).until(ec.presence_of_element_located((By.XPATH, UI_Constant.home_button)))
                time.sleep(3)
                WebDriverWait(self.driver, 60).until(ec.presence_of_element_located( (By.XPATH, UI_Constant.search_button))).click()  # wait for search to load
                time.sleep(5)
                self.driver.find_element(By.XPATH,'//*[@id="root"]/div[1]/div/div[1]/div[2]/div/div[1]/div/input').send_keys('Court Cam')  # search box
                ##self.driver.find_element(By.XPATH,UI_Constant.search_button).send_keys('Court Cam')  # serching for program
                time.sleep(3)

                self.driver.find_element(By.XPATH,
                                        '//*[@id="root"]/div[1]/div/div[1]/div[2]/div/div[3]/div/div/div[1]/div/div').click()  # on demand program
                time.sleep(7)
                self.driver.find_element(By.XPATH,
                                         '/html/body/div[5]/div[3]/div/div/div/div[3]/div[1]/button').click()  # play
                time.sleep(7)
                self.driver.find_element(By.XPATH,
                                         '/html/body/div[6]/div[2]/div/div/button[1]').click()  # a&e
                time.sleep(4)
                self.driver.switch_to.window(self.driver.window_handles[0])  # Switch to previous tab
                time.sleep(5)
                self.driver.find_element(By.XPATH, '/html/body/div[6]/div[2]/div/button').click()  # x close
                time.sleep(5)
                self.driver.find_element(By.XPATH, '/html/body/div[5]/div[3]/div/button').click()  # x close
                time.sleep(5)
                self.driver.find_element(By.XPATH, '//*[@id="root"]/div[1]/div/div[1]/div[2]/div/div[2]/div[1]/button').click()  # clear all
                time.sleep(5)
                self.driver.find_element(By.XPATH,
                                         '//*[@id="root"]/div[1]/div/div[1]/div[2]/div/div[1]/div/input').is_displayed()  # box is present
                self.driver.find_element(By.XPATH,
                                         '//*[@id="root"]/div[1]/div/div[1]/div[2]/div/div[3]/div[2]/p').is_displayed()  # on demand wording



            except NoSuchElementException:
                self.driver.save_screenshot(self.direct + self.name + ".png")
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Chrome",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "element_not_found": 1,
                        }
                    }
                ]
                client_setup.write(bucket=influxdb_bucket, org=influxdb_org, record=body)
                assert False, "Element was not found"
            except TimeoutException:
                self.driver.save_screenshot(self.direct + self.name + ".png")
                loading_circle = self.driver.find_elements(By.XPATH,
                                                           '//div[@class="nvI2gN1AMYiKwYvKEdfIc schema_accent_border-bottom schema_accent_border-right schema_accent_border-left"]')
                no_streaming = self.driver.find_elements(By.XPATH,
                                                         '//h1[contains(text(), "It appears that you are not able to connect to Streaming Services at this time.")]')
                error_404 = self.driver.find_elements(By.XPATH, '//h1[contains(text(), "Oops! Error 404")]')
                loading_element = self.driver.find_elements(By.XPATH, '//span[contains(text(), "Loading...")]')
                went_wrong = self.driver.find_elements(By.XPATH,
                                                       '//h2[contains(text(), "Something went wrong with the stream.")]')
                if len(loading_circle) > 0:
                    body = [
                        {
                            "measurement": "OnStream",
                            "tags": {
                                "Software": onstream_version,
                                "Test": 1,
                                "Pytest": self.name,
                                "URL": onstream_url,
                                "Browser": "Chrome",
                                "Device": device,
                            },
                            "time": time.time_ns(),
                            "fields": {
                                "loading_circle": 1,
                            }
                        }
                    ]
                    client_setup.write(bucket=influxdb_bucket, org=influxdb_org, record=body)
                    assert False, "Stuck on loading screen"
                elif len(no_streaming) > 0:
                    body = [
                        {
                            "measurement": "OnStream",
                            "tags": {
                                "Software": onstream_version,
                                "Test": 1,
                                "Pytest": self.name,
                                "URL": onstream_url,
                                "Browser": "Chrome",
                                "Device": device,
                            },
                            "time": time.time_ns(),
                            "fields": {
                                "unable_to_connect": 1,
                            }
                        }
                    ]
                    client_setup.write(bucket=influxdb_bucket, org=influxdb_org, record=body)
                    assert False, "It appears that you are not able to connect to Streaming Services at this time."
                elif len(error_404) > 0:
                    body = [
                        {
                            "measurement": "OnStream",
                            "tags": {
                                "Software": onstream_version,
                                "Test": 1,
                                "Pytest": self.name,
                                "URL": onstream_url,
                                "Browser": "Chrome",
                                "Device": device,
                            },
                            "time": time.time_ns(),
                            "fields": {
                                "error_404": 1,
                            }
                        }
                    ]
                    client_setup.write(bucket=influxdb_bucket, org=influxdb_org, record=body)
                    assert False, "404 error"
                elif len(loading_element):
                    body = [
                        {
                            "measurement": "OnStream",
                            "tags": {
                                "Software": onstream_version,
                                "Test": 1,
                                "Pytest": self.name,
                                "URL": onstream_url,
                                "Browser": "Chrome",
                                "Device": device,
                            },
                            "time": time.time_ns(),
                            "fields": {
                                "element_loading": 1,
                            }
                        }
                    ]
                    client_setup.write(bucket=influxdb_bucket, org=influxdb_org, record=body)
                    assert False, "Stuck loading an element"
                elif len(went_wrong):
                    body = [
                        {
                            "measurement": "OnStream",
                            "tags": {
                                "Software": onstream_version,
                                "Test": 1,
                                "Pytest": self.name,
                                "URL": onstream_url,
                                "Browser": "Chrome",
                                "Device": device,
                            },
                            "time": time.time_ns(),
                            "fields": {
                                "went_wrong": 1,
                            }
                        }
                    ]
                    client_setup.write(bucket=influxdb_bucket, org=influxdb_org, record=body)
                    assert False, "Something went wrong"
                else:
                    body = [
                        {
                            "measurement": "OnStream",
                            "tags": {
                                "Software": onstream_version,
                                "Test": 1,
                                "Pytest": self.name,
                                "URL": onstream_url,
                                "Browser": "Chrome",
                                "Device": device,
                            },
                            "time": time.time_ns(),
                            "fields": {
                                "timeout_exception": 1,
                            }
                        }
                    ]
                    client_setup.write(bucket=influxdb_bucket, org=influxdb_org, record=body)
                    assert False, "timeout error"





@pytest.mark.usefixtures("setup", "directory")
class TestSettings:
    def test_settings(self, onstream_version, onstream_url,influxdb_bucket,influxdb_org,client_setup ):
        try:
            WebDriverWait(self.driver, 60).until(ec.presence_of_element_located((By.XPATH, UI_Constant.home_button)))  # Wait for the Home Page to Load
            time.sleep(2)
            self.driver.find_element(By.XPATH, '//*[@id="HEADER_CONTAINER"]/div[2]/nav/div/button[5]').click()  # settings new
            time.sleep(3)
            self.driver.find_element(By.XPATH,'//*[@id="root"]/div[1]/div/div[1]/div[2]/div/div/div[2]/div/div/div[5]/button[1]/div[2]/div/label/div').click()  # Enable large font size
            time.sleep(3)
            WebDriverWait(self.driver, 60).until(ec.presence_of_element_located((By.XPATH, UI_Constant.tv_guide))).click()  # tv guide
            time.sleep(3)
            self.driver.find_element(By.XPATH,'//*[@id="HEADER_CONTAINER"]/div[2]/nav/div/button[5]').click()  # settings new
            self.driver.find_element(By.XPATH,'//*[@id="root"]/div/div/div[1]/div[2]/div/div/div[2]/div/div/div[5]/button[1]').click()  # Time Format
            time.sleep(3)
            self.driver.find_element(By.XPATH,'//*[@id="root"]/div[1]/div/div[1]/div[2]/div/div/div[2]/div/div/div[5]/button[2]/div[2]/img').click()  # 24 hour
            time.sleep(2)
            WebDriverWait(self.driver, 60).until(ec.presence_of_element_located((By.XPATH, UI_Constant.tv_guide))).click()  # tv guide
            time.sleep(3)
            self.driver.find_element(By.XPATH,  '//*[@id="HEADER_CONTAINER"]/div[2]/nav/div/button[5]').click()  # settings new
            time.sleep(3)
            self.driver.find_element(By.XPATH, '//*[@id="FAQS"]').click()  # FAQ
            time.sleep(3)
            self.driver.find_element(By.XPATH, '//*[@id="LEGAL"]').click()  # legal and about
            time.sleep(3)

        except NoSuchElementException:
            self.driver.save_screenshot(self.direct + self.name + ".png")
            body = [
                {
                    "measurement": "OnStream",
                    "tags": {
                        "Software": onstream_version,
                        "Test": 1,
                        "Pytest": self.name,
                        "URL": onstream_url,
                        "Browser": "Chrome",
                        "Device": device,
                    },
                    "time": time.time_ns(),
                    "fields": {
                        "element_not_found": 1,
                    }
                }
            ]
            client_setup.write(bucket=influxdb_bucket, org=influxdb_org, record=body)
            assert False, "Element was not found"
        except TimeoutException:
            self.driver.save_screenshot(self.direct + self.name + ".png")
            loading_circle = self.driver.find_elements(By.XPATH,
                                                       '//div[@class="nvI2gN1AMYiKwYvKEdfIc schema_accent_border-bottom schema_accent_border-right schema_accent_border-left"]')
            no_streaming = self.driver.find_elements(By.XPATH,
                                                     '//h1[contains(text(), "It appears that you are not able to connect to Streaming Services at this time.")]')
            error_404 = self.driver.find_elements(By.XPATH, '//h1[contains(text(), "Oops! Error 404")]')
            loading_element = self.driver.find_elements(By.XPATH, '//span[contains(text(), "Loading...")]')
            went_wrong = self.driver.find_elements(By.XPATH,
                                                   '//h2[contains(text(), "Something went wrong with the stream.")]')
            if len(loading_circle) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Chrome",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "loading_circle": 1,
                        }
                    }
                ]
                client_setup.write(bucket=influxdb_bucket, org=influxdb_org, record=body)
                assert False, "Stuck on loading screen"
            elif len(no_streaming) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Chrome",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "unable_to_connect": 1,
                        }
                    }
                ]
                client_setup.write(bucket=influxdb_bucket, org=influxdb_org, record=body)
                assert False, "It appears that you are not able to connect to Streaming Services at this time."
            elif len(error_404) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Chrome",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "error_404": 1,
                        }
                    }
                ]
                client_setup.write(bucket=influxdb_bucket, org=influxdb_org, record=body)
                assert False, "404 error"
            elif len(loading_element):
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Chrome",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "element_loading": 1,
                        }
                    }
                ]
                client_setup.write(bucket=influxdb_bucket, org=influxdb_org, record=body)
                assert False, "Stuck loading an element"
            elif len(went_wrong):
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Chrome",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "went_wrong": 1,
                        }
                    }
                ]
                client_setup.write(bucket=influxdb_bucket, org=influxdb_org, record=body)
                assert False, "Something went wrong"
            else:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Chrome",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "timeout_exception": 1,
                        }
                    }
                ]
                client_setup.write(bucket=influxdb_bucket, org=influxdb_org, record=body)
                assert False, "timeout error"


