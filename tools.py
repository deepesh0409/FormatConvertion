from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import StreamingResponse, JSONResponse
from typing import Optional
from PIL import Image, ImageDraw, ImageFont
import io
import os
import numpy as np
import pillow_heif # <--- ADD THIS

# Teach Pillow how to read Apple iPhone HEIC files!
pillow_heif.register_heif_opener()

router = APIRouter()

@router.post("/image-process")
async def image_process(
    file: UploadFile = File(...),
    tool: str = Form(...),
    extra_param: Optional[str] = Form("") # <--- Added for Watermark Text
):
    try:
        # Load image into memory
        contents = await file.read()
        img = Image.open(io.BytesIO(contents))
        output = io.BytesIO()
        original_name = os.path.splitext(file.filename)[0]

        # 1. JPG to PNG
        if tool == "jpg-to-png":
            img = img.convert("RGBA")
            img.save(output, format="PNG")
            filename = f"{original_name}.png"
            media_type = "image/png"

        # 2. PNG to JPG
        elif tool == "png-to-jpg":
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            else:
                img = img.convert("RGB")
            img.save(output, format="JPEG", quality=95)
            filename = f"{original_name}.jpg"
            media_type = "image/jpeg" 

        # 3. Compress
        elif tool == "compress":
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            else:
                img = img.convert("RGB")
            img.save(output, format="JPEG", quality=60, optimize=True)
            filename = f"{original_name}_compressed.jpg"
            media_type = "image/jpeg"    

        # 4. Remove Background
        elif tool == "bg-remove":
            from rembg import remove
            img_bytes = io.BytesIO()
            img.save(img_bytes, format='PNG')
            output_bytes = remove(img_bytes.getvalue())
            output = io.BytesIO(output_bytes)
            filename = f"{original_name}_nobg.png"
            media_type = "image/png"

        # 5. Blur Face
        elif tool == "blur-face":
            import cv2
            open_cv_image = np.array(img.convert('RGB'))
            open_cv_image = open_cv_image[:, :, ::-1].copy() 

            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            gray = cv2.cvtColor(open_cv_image, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.1, 4)
            
            for (x, y, w, h) in faces:
                roi = open_cv_image[y:y+h, x:x+w]
                roi = cv2.GaussianBlur(roi, (99, 99), 30)
                open_cv_image[y:y+h, x:x+w] = roi

            open_cv_image = cv2.cvtColor(open_cv_image, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(open_cv_image)
            img.save(output, format="PNG")
            filename = f"{original_name}_blurred.png"
            media_type = "image/png"

        # 6. AI Image Upscaler
        elif tool == "upscale":
            new_width = int(img.width * 2)
            new_height = int(img.height * 2)
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            from PIL import ImageEnhance
            enhancer = ImageEnhance.Sharpness(img)
            img = enhancer.enhance(1.5)
            img.save(output, format="PNG")
            filename = f"{original_name}_upscaled.png"
            media_type = "image/png"

        # 7. Add Watermark (NEW)
        elif tool == "watermark":
            text = extra_param if extra_param else "FormatConverter"
            img = img.convert('RGBA')
            txt_layer = Image.new('RGBA', img.size, (255, 255, 255, 0))
            draw = ImageDraw.Draw(txt_layer)
            
            # Make the text responsive to the image size
            font_size = max(int(img.width / 10), 20)
            try:
                # Try to use standard Windows Arial font
                font = ImageFont.truetype("arial.ttf", font_size)
            except:
                font = ImageFont.load_default()
                
            # Calculate text size and center it
            bbox = draw.textbbox((0, 0), text, font=font)
            text_w = bbox[2] - bbox[0]
            text_h = bbox[3] - bbox[1]
            x = (img.width - text_w) / 2
            y = (img.height - text_h) / 2
            
            # Draw semi-transparent white text
            draw.text((x, y), text, font=font, fill=(255, 255, 255, 128))
            
            img = Image.alpha_composite(img, txt_layer)
            img = img.convert("RGB") # Convert back to RGB to save as JPG/PNG
            img.save(output, format="PNG")
            filename = f"{original_name}_watermarked.png"
            media_type = "image/png"

        # 8. Auto Watermark Remover (NEW)
        elif tool == "wm-remover":
            import cv2
            # Convert to OpenCV format
            open_cv_image = np.array(img.convert('RGB'))
            open_cv_image = open_cv_image[:, :, ::-1].copy() # RGB to BGR
            
            # Simple heuristic: Auto-detect bright/white semi-transparent text
            gray = cv2.cvtColor(open_cv_image, cv2.COLOR_BGR2GRAY)
            # Find the brightest pixels (often white watermarks)
            _, mask = cv2.threshold(gray, 220, 255, cv2.THRESH_BINARY)
            
            # Thicken the mask slightly to cover edges perfectly
            kernel = np.ones((5, 5), np.uint8)
            mask = cv2.dilate(mask, kernel, iterations=1)
            
            # AI-assisted Inpainting (uses surrounding pixels to fill the watermark gap)
            result = cv2.inpaint(open_cv_image, mask, 3, cv2.INPAINT_TELEA)
            
            result = cv2.cvtColor(result, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(result)
            img.save(output, format="PNG")
            filename = f"{original_name}_cleaned.png"
            media_type = "image/png"
            
        # 9. Compress to Exact KB (NEW)
        elif tool == "compress-exact":
            try:
                target_kb = float(extra_param)
            except:
                target_kb = 50.0 # Default to 50KB if user types nothing
                
            target_bytes = int(target_kb * 1024)
            
            # Convert to RGB (JPEG is mandatory for extreme compression)
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            else:
                img = img.convert("RGB")

        # 10. HEIC to JPG (NEW)
        elif tool == "heic-to-jpg":
            # If the image has transparency or is weirdly formatted, composite it on white
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            else:
                img = img.convert("RGB")
                
            img.save(output, format="JPEG", quality=95)
            filename = f"{original_name}.jpg"
            media_type = "image/jpeg"
            
            # Step 1: Binary search to find the highest quality that fits the size
            low, high = 5, 95
            best_quality = 5
            
            while low <= high:
                mid = (low + high) // 2
                temp_out = io.BytesIO()
                img.save(temp_out, format="JPEG", quality=mid, optimize=True)
                
                if temp_out.tell() <= target_bytes:
                    best_quality = mid
                    low = mid + 1 # Try to get higher quality
                else:
                    high = mid - 1 # Quality is too high, size is too big

        # 11. Image to WebP (NEW)
        elif tool == "to-webp":
            # WebP natively supports transparency (RGBA), so we just convert it directly!
            # If the image is a weird format like Palette (P), convert to RGBA to be safe.
            if img.mode not in ('RGB', 'RGBA'):
                img = img.convert('RGBA')
            
            # Save as WebP (quality=80 is the standard sweet spot for WebP)
            img.save(output, format="WEBP", quality=80, method=4)
            filename = f"{original_name}.webp"
            media_type = "image/webp"

        # 12. Extract Text from Image (OCR)
        
            
            # Apply the best found quality
            img.save(output, format="JPEG", quality=best_quality, optimize=True)
            
            # Step 2: If even quality=5 is too big, we must reduce the physical dimensions
            while output.tell() > target_bytes:
                new_width = int(img.width * 0.9) # Shrink by 10%
                new_height = int(img.height * 0.9)
                if new_width < 10 or new_height < 10:
                    break # Safety escape
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                output = io.BytesIO() # Reset buffer
                img.save(output, format="JPEG", quality=best_quality, optimize=True)
                
            filename = f"{original_name}_{int(target_kb)}KB.jpg"
            media_type = "image/jpeg"

        else:
            return JSONResponse(status_code=400, content={"error": f"Unsupported tool: {tool}"})
        
        output.seek(0)
        return StreamingResponse(
            output,
            media_type=media_type,
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )
    
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"Processing failed: {str(e)}"})