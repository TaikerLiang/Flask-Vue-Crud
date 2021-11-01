import io

from anticaptchaofficial.imagecaptcha import *
import PIL.Image as Image


class CaptchaSolverService:
    API_KEY = "fbe73f747afc996b624e8d2a95fa0f84"

    def __init__(self):
        self.solver = imagecaptcha()
        self.solver.set_verbose(1)
        self.solver.set_key(self.API_KEY)

    def solve_image(self, image_content=None, file_path="") -> str:
        if image_content:
            file_name = "captcha.jpeg"
            image = Image.open(io.BytesIO(image_content))
            image.save(file_name)

            captcha_text = self.solver.solve_and_return_solution(file_name)
            if captcha_text != 0:
                return captcha_text
            else:
                print("task finished with error ", self.solver.error_code)
                return ""
        else:
            captcha_text = self.solver.solve_and_return_solution(file_path)
            if captcha_text != 0:
                return captcha_text
            else:
                print("task finished with error ", self.solver.error_code)
                return ""
