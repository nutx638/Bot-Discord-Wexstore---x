import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
import json
import os
from dotenv import load_dotenv

# โหลดค่า Token จาก .env
load_dotenv()  # โหลดค่าจากไฟล์ .env
TOKEN = os.getenv("DISCORD_TOKEN")  # ดึง token จาก Environment Variable

intents = discord.Intents.default()
intents.message_content = True

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        await self.tree.sync()  # ทำการ sync คำสั่ง

bot = MyBot()

# เก็บข้อมูลใน List
data_list = []

# ฟังก์ชั่นในการบันทึกข้อมูลลงในไฟล์ JSON
def save_data():
    with open("data.json", "w") as f:
        json.dump(data_list, f)

# ฟังก์ชั่นในการโหลดข้อมูลจากไฟล์ JSON
def load_data():
    global data_list
    if os.path.exists("data.json"):
        with open("data.json", "r") as f:
            data_list = json.load(f)

class AddDataModal(discord.ui.Modal, title="📋 ADD NEW DATA"):
    user_facebook = discord.ui.TextInput(label="📘 Facebook Name", placeholder="Enter Facebook name...")
    diamon = discord.ui.TextInput(label="💎 Diamond Amount (Optional)", placeholder="Enter diamond amount...", required=False)
    star = discord.ui.TextInput(label="⭐ Star Amount (Optional)", placeholder="Enter star amount...", required=False)
    amount = discord.ui.TextInput(label="💰 Amount", placeholder="Enter total amount...")
    user_ingame = discord.ui.TextInput(label="🎮 In-Game Name", placeholder="Enter in-game name...")

    async def on_submit(self, interaction: discord.Interaction):
        """เมื่อกด Submit"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # สร้าง dictionary สำหรับข้อมูลที่กรอก
        data = {
            "facebook": self.user_facebook.value,
            "amount": self.amount.value,
            "ingame": self.user_ingame.value,
            "time": timestamp
        }

        # เพิ่มข้อมูล diamon ถ้ามีการกรอก
        if self.diamon.value:
            data["diamon"] = self.diamon.value

        # เพิ่มข้อมูล star ถ้ามีการกรอก
        if self.star.value:
            data["star"] = self.star.value

        # เก็บข้อมูลลงใน data_list
        data_list.append(data)
        
        # บันทึกข้อมูลลงไฟล์ JSON
        save_data()

        # สร้างข้อความตอบกลับ
        success_message = "```diff\n+ ✅ เพิ่มข้อมูลสำเร็จ!\n"
        success_message += f"+ 📘 Facebook: {self.user_facebook.value}\n"
        success_message += f"+ 💰 Amount: {self.amount.value}\n"
        success_message += f"+ 🎮 In-Game: {self.user_ingame.value}\n"
        success_message += f"+ 📅 Time: {timestamp}\n"
        
        # แสดงข้อมูล diamon และ star ถ้ามี
        if 'diamon' in data:
            success_message += f"+ 💎 Diamond: {data['diamon']}\n"
        if 'star' in data:
            success_message += f"+ ⭐ Star: {data['star']}\n"

        success_message += "```"

        await interaction.response.send_message(success_message, ephemeral=True)

class DataView(discord.ui.View):
    """UI สำหรับแสดงปุ่ม Add, Remove, Show"""
    def __init__(self):
        super().__init__(timeout=None)

    async def check_permissions(self, interaction: discord.Interaction) -> bool:
        """ฟังก์ชันตรวจสอบสิทธิ์"""
        if not any(role.name == "👑" for role in interaction.user.roles):  # เปลี่ยน "Admin" เป็นชื่อ role ที่ต้องการ
            await interaction.response.send_message("คุณไม่มีสิทธิ์ใช้งานคำสั่งนี้!", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="🚀 ADD", style=discord.ButtonStyle.green, custom_id="add_button")
    async def add_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """กดปุ่มแล้วเปิดแบบฟอร์ม"""
        if not await self.check_permissions(interaction):
            return  # ถ้าไม่มีสิทธิ์จะหยุดการทำงานของปุ่มนี้

        await interaction.response.send_modal(AddDataModal())

    @discord.ui.button(label="❌ REMOVE", style=discord.ButtonStyle.red, custom_id="remove_button")
    async def remove_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """ปุ่ม Remove"""
        if not await self.check_permissions(interaction):
            return  # ถ้าไม่มีสิทธิ์จะหยุดการทำงานของปุ่มนี้

        if not data_list:
            await interaction.response.send_message("```diff\n- ❌ ไม่พบข้อมูลที่สามารถลบได้!\n```", ephemeral=True)
            return

        # สร้าง list ของข้อมูลให้เลือก
        options = [discord.SelectOption(label=f"ข้อมูล {i+1}: {data['facebook']} - {data['ingame']}", value=str(i)) for i, data in enumerate(data_list)]
        select = discord.ui.Select(placeholder="เลือกข้อมูลที่ต้องการลบ", options=options)

        # ฟังก์ชั่นในการเลือกข้อมูลจาก list
        async def select_callback(interaction: discord.Interaction):
            index_to_remove = int(select.values[0])
            removed_data = data_list.pop(index_to_remove)  # ลบข้อมูลที่เลือก
            save_data()  # บันทึกข้อมูลหลังจากลบ
            await interaction.response.send_message(f"```diff\n+ ✅ ลบข้อมูลสำเร็จ:\n- Facebook: {removed_data['facebook']}\n- In-Game: {removed_data['ingame']}\n```", ephemeral=True)

        select.callback = select_callback

        # ส่ง select ไปให้ผู้ใช้เลือก
        await interaction.response.send_message("เลือกข้อมูลที่ต้องการลบ:", view=discord.ui.View().add_item(select))

    @discord.ui.button(label="📜 SHOW", style=discord.ButtonStyle.blurple, custom_id="show_button")
    async def show_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """ปุ่ม Show"""
        if not await self.check_permissions(interaction):
            return  # ถ้าไม่มีสิทธิ์จะหยุดการทำงานของปุ่มนี้

        if not data_list:
            await interaction.response.send_message("📂 **No Data Found!**", ephemeral=True)
            return

        message = "```diff\n+ 📜 รายการที่บันทึกไว้:\n```\n"
        for i, data in enumerate(data_list):
            message += (
                "```diff\n"
                "+ ✅ เพิ่มข้อมูลสำเร็จ!\n"
                f"+ 📘 Facebook: {data['facebook']}\n"
                f"+ 💰 Amount: {data['amount']}\n"
                f"+ 🎮 In-Game: {data['ingame']}\n"
                f"+ 📅 Time: {data['time']}\n"
            )

            # แสดงข้อมูล diamon และ star ถ้ามี
            if 'diamon' in data:
                message += f"+ 💎 Diamond: {data['diamon']}\n"
            if 'star' in data:
                message += f"+ ⭐ Star: {data['star']}\n"
            
            message += "```\n"

        # ส่งข้อความไปยังช่องที่แสดงผล
        await interaction.response.send_message(message, ephemeral=False)


# ส่วนของคำสั่ง setup ที่ไม่เปลี่ยนแปลง
@bot.tree.command(name="setup", description="สร้าง UI สำหรับ Add/Remove/Show")
async def setup(interaction: discord.Interaction):
    # ตรวจสอบว่า user ที่เรียกคำสั่งมี role ที่เหมาะสมหรือไม่
    if not any(role.name == "👑" for role in interaction.user.roles):  # เปลี่ยน "Admin" เป็นชื่อ role ที่ต้องการ
        await interaction.response.send_message("คุณไม่มีสิทธิ์ใช้งานคำสั่งนี้!", ephemeral=True)
        return

    embed = discord.Embed(
        title="⚠️ WEXSTORE MANAGER ⭐",
        description="🟢 MANAGER DATA WEXSTORE.FARM 💻",
        color=discord.Color.blue()
    )
    embed.set_footer(text="by NutX")
    
    # ✅ เพิ่ม GIF URL ที่ด้านล่างของ UI
    embed.set_image(url="https://img2.pic.in.th/pic/11110e8683e16b8b92df.gif")  

    view = DataView()
    await interaction.response.send_message(embed=embed, view=view)




@bot.event
async def on_ready():
    load_data()  # โหลดข้อมูลเมื่อบ็อตเริ่มทำงาน
    print("Bot is ready!")

bot.run(TOKEN)  # ใช้ Token จาก .env
