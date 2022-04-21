import abc
import io
from pathlib import Path

import PIL.Image as Image
from anticaptchaofficial.imagecaptcha import *
from anticaptchaofficial.recaptchav2proxyless import *

from crawler.core.exceptions_new import SuspiciousOperationError


class AntiCaptchaService:
    API_KEY = "fbe73f747afc996b624e8d2a95fa0f84"

    def __init__(self, solver):
        if not solver:
            raise SuspiciousOperationError(reason="Invalid solver for anticaptcha")
        self.solver = solver
        self.solver.set_verbose(1)
        self.solver.set_key(self.API_KEY)

    @abc.abstractmethod
    def solve(self):
        pass


class ImageAntiCaptchaService(AntiCaptchaService):
    def __init__(self):
        super().__init__(solver=imagecaptcha())

    def solve(self, image_content: bytes = None, file_path: Path = "") -> str:
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

        if file_path:
            captcha_text = self.solver.solve_and_return_solution(file_path)
            if captcha_text != 0:
                return captcha_text
            else:
                print("task finished with error ", self.solver.error_code)
                return ""


class GoogleRecaptchaV2Service(AntiCaptchaService):
    def __init__(self):
        super().__init__(solver=recaptchaV2Proxyless())

    def solve(self, g_url: str, g_site_key: str) -> str:
        self.solver.set_website_url(g_url)
        self.solver.set_website_key(g_site_key)

        g_response = self.solver.solve_and_return_solution()
        if g_response != 0:
            print(f"g-response: {g_response}")
            return g_response
        else:
            print(f"task finished with error {self.solver.error_code}")
            return ""
