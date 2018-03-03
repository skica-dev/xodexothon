import argparse
import os
import re
from datetime import datetime
from subprocess import call, DEVNULL

import PyPDF2
import requests

coupons_writer = PyPDF2.PdfFileWriter()


def fetch_coupon(num):
    """
    fetches given coupon from Sodexo
    :param num: number of coupon to be appended to url
    :return: that coupon content
    """
    cnr = "{:02d}".format(num)
    url = "https://dlaciebie.sodexo.pl/ekupony/drukuj/id/" + cnr
    coupon = requests.get(url)
    return coupon.content


def check_coupon(coupon):
    """
    checks if a given coupon content is a valid coupon
    :param coupon: coupon content
    :return: True if coupon content is valid (not a 404 page and not a blank page)
    """
    return len(coupon) != 52286 and len(coupon) != 1008  # 52286 -> size of a 404 page, 1008 -> size of an empty pdf


def save_coupon(coupon, destination, master_dest):
    """
    saves given coupon at a destination
    :param coupon: valid coupon content
    :param destination: destination of the coupon pdf
    :param master_dest: destination of the master coupon file with all coupons as pages
    """
    with open(destination, "wb") as f:
        f.write(coupon)
    add_coupon(destination, master_dest)


def add_coupon(source, destination):
    """
    copies source coupon as a page to a master file of coupons
    :param source: source of the copied coupon
    :param destination: destination of the master file of coupons
    """
    if not check_date(source):
        return
    with open(source, "rb") as f:
        coupon_reader = PyPDF2.PdfFileReader(f)
        page = coupon_reader.getPage(0)
        coupons_writer.addPage(page)
        save_coupons(destination)


def check_date(coupon):
    """
    checks if coupon has expired
    :param coupon: coupon pdf path
    :return: True if coupon is not expired
    """
    call(["ebook-convert", coupon, "txt_temp.txt"], stdout=DEVNULL)
    with open("txt_temp.txt") as f:
        text = f.read()
        date = re.search("Ważny.* do (.*) r\.", text)
        expires = date.groups()[0]
        exp_date = datetime.strptime(expires, "%d.%m.%Y")
        return exp_date > datetime.now()


def save_coupons(destination):
    """
    saves master file of coupons
    :param destination: destination of the master file of coupons
    """
    with open(destination, "wb") as f:
        coupons_writer.write(f)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Downloads Sodexo coupons.")
    parser.add_argument("coupons", metavar='N', type=int, help="maximal coupon number")
    arg = parser.parse_args()

    try:
        os.makedirs(os.path.join(os.pardir, "coupons"))
    except OSError:
        pass

    for i in range(arg.coupons):
        coup = fetch_coupon(i)
        if check_coupon(coup):
            save_coupon(coup, os.path.join(os.pardir, "coupons", "coupon{}.pdf".format(i)),
                        os.path.join(os.pardir, "coupons", "coupons.pdf"))
