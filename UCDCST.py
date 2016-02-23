from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import selenium.common.exceptions as sexceptions
import getpass
import os
import time


class UCDavisCourseSelectionTool:
    def __init__(self, username, password):
        # self.driver = webdriver.Chrome(os.path.join(os.path.dirname(__file__), "chromedriver"))
        self.driver = webdriver.PhantomJS(os.path.join(os.path.dirname(__file__), "phantomjs"))
        self.driver.set_window_size(1124, 850)
        self.username = username
        self.password = password
        self.login_url = "https://cas.ucdavis.edu/cas/login?service=https%3A%2F%2Fmy%2Eucdavis" \
                         "%2Eedu%2Fschedulebuilder%2Findex%2Ecfm%3FtermCode%3D201603"
        self.driver_wait = WebDriverWait(self.driver, 5)
        self.log_in()
        self.crn_list = self.check_current_course_no_print()

    def log_in(self):
        self.driver.get(self.login_url)
        login_username = self.driver.find_element_by_id("username")
        login_password = self.driver.find_element_by_id("password")
        login_username.send_keys(self.username)
        login_password.send_keys(self.password)
        self.driver.find_element_by_name("submit").click()
        # time.sleep(1.5)
        self.driver_wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//div[@class = 'BtnGrpGold menu2']//a[@class = 'btn add_search_courses_trigger']")
            )
        )

    def select_course(self, crn):
        # the course must already in the dashboard, so when calling this function, we need to check
        # whether it is in, by the checking function, or just called after the search_course function.
        crn = str(crn)
        self.driver.find_element_by_id(crn + "_ActionMenuTrigger").click()
        self.driver.find_element_by_xpath("//ul[@id = '" + crn +
                                          "_ActionMenu']//a[@title = 'Register for this course.']").click()

    def waitlist_course(self, crn):
        # This function just waitlist the course by first selecting it, then allow waitlist
        crn = str(crn)
        self.driver.find_element_by_id(crn + "_ActionMenuTrigger").click()
        self.driver.find_element_by_xpath("//ul[@id = '" + crn +
                                          "_ActionMenu']//a[contains(title, 'Waitlist')]").click()
        self.driver.find_element_by_xpath("//div[@class = 'modal-content']//button[contains(., 'Yes')]").click()

    def search_course(self, crn, save_flag=False):
        # fill out the form
        crn = str(crn)
        self.driver.find_element_by_xpath("//div[@class = 'BtnGrpGold menu2']//"
                                          "a[@class = 'btn add_search_courses_trigger']").click()
        course_number = self.driver.find_element_by_id("course_number")
        course_number.clear()
        course_number.send_keys(crn)

        # after filling all info, search
        search_field = "//div[@id = 'CoursesSearch']"
        self.driver.find_element_by_xpath(search_field + "//button[@class = 'btn btn-primary']").click()
        self.driver_wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@id = 'CoursesSearch']"
                                                                     "//button[contains(., 'Details')]")))

        # retrieve all the information, and print them out
        section_count, crn_list = self.show_course_statistics()

        return_value = 0

        if save_flag:
            user_input = int(input("Please tell me which section you want to choose, from section 1 to section " +
                                   str(section_count) +
                                   " , listed above, or type 0 to give up choosing this time\n"))
            while user_input not in range(section_count + 1):
                user_input = int(input("This section is not available, please type in another one\n"))
            if user_input == 0:
                pass
            else:
                return_value = crn_list[user_input - 1]
        # close
        self.driver.find_element_by_xpath(search_field + "//button[@class = 'close closer']").click()

        # return crn if search one course and put it on the dashboard, otherwise 0
        return return_value

    def hide_show_course(self, section_count):
        # This function is used to identify different sections of the same course, and retrieve all the information
        # then store them into a dictionary
        prior_path = "//div[@id = 'CoursesSearch']//div[@class = 'data-item'][" + str(section_count) + "]"
        # show details
        self.driver.find_element(By.XPATH, prior_path + "//button[contains(., 'Details')]").click()
        print("---------------------------------------------------------------------------------")
        print("This is section " + str(section_count))
        print("\n")

        # extract information
        # # basic info
        info_list = self.driver.find_element(By.XPATH, prior_path).text.split("\n")
        info_list_name = ["CRN", "Course", "Course Name", "Open / Waitlist",
                          "Units", "Instructor", "Lecture"]
        info_list_value = info_list[0:6]
        # # lecture info
        info_list_lecture_index = info_list.index("Lecture")
        info_list_lecture_value = '  '.join(info_list[info_list_lecture_index - 2:info_list_lecture_index + 2])
        info_list_value.append(info_list_lecture_value)
        # # discussion info
        try:
            info_list_dic_index = info_list.index("Discussion")
            info_list_dic_value = '  '.join(info_list[info_list_dic_index - 2:info_list_dic_index + 2])
            info_list_value.append(info_list_dic_value)
            info_list_name.append("Discussion")
        except:
            pass
        # # print them out
        info_dict = dict(zip(info_list_name, info_list_value))
        for i in info_list_name:
            print(i + ": " + str(info_dict[i]))

        # course detail information
        print(self.driver.find_element(By.XPATH, prior_path + "//div[@class = 'details']").text)
        print("---------------------------------------------------------------------------------")

        # hide details
        self.driver.find_element(By.XPATH, prior_path + "//button[contains(., 'Details')]").click()

        # return crn for selecting
        return info_dict["CRN"]

    def show_course_statistics(self):
        # retrieve all the information, and print them out
        section_count = 1
        crn_list = []
        while True:
            try:
                crn = self.hide_show_course(section_count)
                section_count += 1
                crn_list.append(crn)
            except sexceptions.NoSuchElementException:
                break
        return section_count - 1, crn_list

    def check_current_course_no_print(self):
        # This is a non-print version of check_current_course, to check the dashboard courses
        course_count = 1
        crn_list = []
        while True:
            try:
                prior_path = "//div[@id = 'SavedSchedulesListDisplayContainer']" \
                             "/div[@class = 'CourseItem gray-shadow-border clearfix'][" + str(course_count) + "]"
                crn = self.driver.find_element(By.XPATH, prior_path +
                                               "//span[contains(., 'CRN:')]/..").text
                crn_list.append(crn)
                course_count += 1
            except sexceptions.NoSuchElementException:
                break
        return crn_list

    def check_current_course(self):
        # we need to check the current course of the client, and print them out
        course_count = 1
        crn_list = []
        print("Your current saved courses include:")
        print("---------------------------------------------------------------------------------")
        while True:
            try:
                prior_path = "//div[@id = 'SavedSchedulesListDisplayContainer']" \
                             "/div[@class = 'CourseItem gray-shadow-border clearfix'][" + str(course_count) + "]"
                print(self.driver.find_element(By.XPATH, prior_path +
                                               "//div[@class = 'classTitle height-justified']").text)
                info_list = self.driver.find_element(By.XPATH, prior_path +
                                                     "//div[@class = 'status-section clearfix']").text
                print(info_list)
                print("---------------------------------------------------------------------------------")

                crn = self.driver.find_element(By.XPATH, prior_path +
                                               "//span[contains(., 'CRN:')]/..").text
                crn_list.append(crn)
                course_count += 1
            except sexceptions.NoSuchElementException:
                break
        print("In total " + str(course_count - 1) + " courses")
        return course_count - 1


if __name__ == "__main__":
    print("Welcome to UCDavisCourseSelectionTool(UCDCST)!")
    print("Thanks for using UCDCST, please follow the instructions below. Have fun!")
    print("\n")
    print("To use UCDCST, you need to supply your username and password. To keep your privacy, UCDCST will"
          "not store your information, nor send them to any servers. It is absolutely safe to use UCDCST. "
          "Moreover, UCDCST will ask your username and password only once, at the beginning of the application. "
          "The password will be unrevealed from anyone, so just type it, and then hit enter.")
    print("\n")
    username_m = input("Please type in your username: ")
    password_m = getpass.getpass('Please type in your password: ')
    print("\n")
    client = UCDavisCourseSelectionTool(username_m, password_m)
    print("You can type in the number before each option to indicate what you would like to do.")
    while True:
        print("\n")
        user_option = input("0. quit\n"
                            "1. show current saved and registered course\n"
                            "2. search course\n"
                            "3. select course\n"
                            "4. waitlist course\n"
                            "5. drop course\n"
                            "\n")
        user_option = int(user_option)
        if user_option == 0:
            print("Thanks again for using UCDCST, hope to see you again!\n")
            break
        elif user_option == 1:
            client.check_current_course()
        elif user_option == 2:
            crn_m = input("Please tell me which course you would like to search. This can be a course CRN, usually "
                          "5 digits, or a course number, for example ECS 60\n")
            client.search_course(crn_m)
        elif user_option == 3:
            crn_m = input("Please tell me which course you would like to select. This can be a course CRN, usually "
                          "5 digits, or a course number, for example ECS 60\n")
            if crn_m not in client.crn_list:
                crn_m = client.search_course(crn_m, True)
            client.select_course(crn_m)
        elif user_option == 4:
            crn_m = input("Please tell me which course you would like to waitlist. This can be a course CRN, usually "
                          "5 digits, or a course number, for example ECS 60\n")
            if crn_m not in client.crn_list:
                crn_m = client.search_course(crn_m, True)
            client.waitlist_course(crn_m)
        elif user_option == 5:
            pass
        else:
            print("Please type in correct number")

    # zz.select_course(63806)
    # zz.search_course("63806", False)
