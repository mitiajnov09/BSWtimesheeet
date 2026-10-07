"""Upload validation and graceful handling of legacy image corruption."""
import base64
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image, PngImagePlugin
from pypdf import PdfReader

import photos
from db import connect, migrate, seed
from domain import Problem
from pdf_export import export


def encoded_image(format='PNG',size=(16,12),**options):
    output=io.BytesIO()
    Image.new('RGB',size,'red').save(output,format=format,**options)
    mime={'PNG':'png','JPEG':'jpeg','WEBP':'webp'}[format]
    return 'data:image/'+mime+';base64,'+base64.b64encode(output.getvalue()).decode(),output.getvalue()


class SecurityImageTests(unittest.TestCase):
    def test_supported_formats_remain_valid_and_metadata_free(self):
        exif=Image.Exif();exif[270]='Private location';exif[271]='Private device'
        pnginfo=PngImagePlugin.PngInfo();pnginfo.add_text('Private','Hidden location')
        for format in ('PNG','JPEG','WEBP'):
            with self.subTest(format=format):
                options={'exif':exif}
                if format=='PNG':options['pnginfo']=pnginfo
                encoded,_=encoded_image(format,**options)
                content,mime=photos.decode(encoded)
                with Image.open(io.BytesIO(content)) as image:
                    image.load()
                    self.assertEqual(image.format,format)
                    self.assertEqual(image.size,(16,12))
                    self.assertFalse(image.getexif())
                    self.assertNotIn('Private',image.info)
                    self.assertNotIn('exif',image.info)
                self.assertEqual(mime,{'PNG':'image/png','JPEG':'image/jpeg','WEBP':'image/webp'}[format])

    def test_exif_orientation_applied_before_metadata_removal(self):
        exif=Image.Exif();exif[274]=6
        encoded,_=encoded_image('JPEG',(10,20),exif=exif)
        content,_=photos.decode(encoded)
        with Image.open(io.BytesIO(content)) as image:
            self.assertEqual(image.size,(20,10))
            self.assertFalse(image.getexif())

    def test_truncated_jpeg_rejected_for_photo_and_screenshot(self):
        _,raw=encoded_image('JPEG',(64,64))
        encoded='data:image/jpeg;base64,'+base64.b64encode(raw[:-2]).decode()
        for label in ('Фотография','Скриншот'):
            with self.subTest(label=label),self.assertRaises(Problem) as context:
                photos.decode(encoded,label=label,max_dimension=2560 if label=='Скриншот' else 1024)
            self.assertEqual(context.exception.status,400)

    def test_dimensions_and_alpha_preserved_with_separate_screenshot_limit(self):
        image=Image.new('RGBA',(3000,600),(10,20,30,75));buffer=io.BytesIO();image.save(buffer,'PNG')
        encoded='data:image/png;base64,'+base64.b64encode(buffer.getvalue()).decode()
        for limit in (1024,2560):
            content,_=photos.decode(encoded,label='Скриншот' if limit==2560 else 'Фотография',max_dimension=limit)
            with Image.open(io.BytesIO(content)) as normalized:
                self.assertEqual(normalized.width,limit)
                self.assertEqual(normalized.getpixel((0,0))[3],75)

    def test_mime_mismatch_and_normalized_output_over_limit_rejected(self):
        encoded,_=encoded_image()
        with self.assertRaises(Problem):photos.decode(encoded.replace('image/png','image/jpeg'))
        def oversized_save(image,buffer,**kwargs):buffer.write(b'x'*(photos.MAX_IMAGE+1))
        with patch.object(Image.Image,'save',oversized_save),self.assertRaises(Problem) as context:
            photos.decode(encoded)
        self.assertEqual(context.exception.status,413)

    def test_corrupt_legacy_portrait_uses_initials_and_pdf_still_opens(self):
        with tempfile.TemporaryDirectory() as directory:
            conn=connect(str(Path(directory)/'test.sqlite'))
            try:
                migrate(conn);seed(conn)
                manager=dict(conn.execute('SELECT * FROM users WHERE id=2').fetchone())
                _,raw=encoded_image('JPEG',(64,64))
                conn.execute('INSERT INTO employee_photos(employee_id,content,mime) VALUES(?,?,?)',(1,raw[:-2],'image/jpeg'))
                with self.assertLogs(level='WARNING') as logs:
                    pdf=export(conn,manager,dict(project_id=1,start='2026-10-01',end='2026-10-14',employee_ids=[1],include_photos=True))
                reader=PdfReader(io.BytesIO(pdf))
                text=' '.join(page.extract_text() for page in reader.pages)
                self.assertIn('JK',text)
                self.assertIn('Kazlauskas',text)
                self.assertEqual(sum(len(page.images) for page in reader.pages),0)
                self.assertEqual(logs.output,['WARNING:root:Skipping invalid stored employee portrait during PDF export'])
            finally:conn.close()


if __name__=='__main__':unittest.main()
