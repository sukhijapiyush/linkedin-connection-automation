import time

import pyautogui
from PIL import Image


def __move_mouse2center(screenshot_rect):
    pyautogui.moveTo(
        screenshot_rect[0] + screenshot_rect[2] / 2.0,
        screenshot_rect[1] + screenshot_rect[3] / 2.0
    )


def scroll_screenshot(screenshot_rect):
    scroll_height = screenshot_rect[3] // 3
    img_clip = []

    __move_mouse2center(screenshot_rect)
    screenshot = pyautogui.screenshot(region=screenshot_rect)
    img_clip.append(screenshot)

    while 1:
        pyautogui.vscroll(-scroll_height)
        time.sleep(1.0)
        new_screenshot = pyautogui.screenshot(region=screenshot_rect)
        tmp_img = img_clip[-1].crop((
            0,
            (img_clip[-1].height // 4) * 3,
            img_clip[-1].width,
            img_clip[-1].height
        ))
        tmp_pos = pyautogui.locate(tmp_img, new_screenshot)
        actual_scroll_height = new_screenshot.height - (tmp_pos[1] + tmp_pos[3])
        if actual_scroll_height == 0:
            break
        else:
            img_clip.append(new_screenshot.crop((
                0,
                tmp_pos[1] + tmp_pos[3],
                new_screenshot.width,
                new_screenshot.height
            )))
            if actual_scroll_height <= (scroll_height // 2.0):
                break

    total_height = sum(img.height for img in img_clip)
    final_image = Image.new("RGB", (screenshot_rect[2], total_height))
    y_offset = 0
    for img in img_clip:
        final_image.paste(img, (0, y_offset))
        y_offset += img.height
    return final_image