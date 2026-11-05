#!/usr/bin/env python3
# Copyright (c) 2026 Christer Törnkvist <christer@borgasundsfotografiska.se>
# SPDX-License-Identifier: GPL-3.0-or-later
"""InkProf ICC — explicit profile assignment and LittleCMS conversion."""
import io
import os
from pathlib import Path
import tempfile
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageCms

from icc_processing import INTENTS, MODES, process, profile_mode, save_image

class App:
    def __init__(self, root):
        self.root = root
        self.image = self.path = self.source = self.target = None
        root.title('InkProf · ICC-konvertering')
        root.geometry('760x570')
        frame = ttk.Frame(root, padding=24)
        frame.pack(fill='both', expand=True)
        frame.columnconfigure(1, weight=1)
        ttk.Label(frame, text='ICC-konvertering', font=('', 24, 'bold')).grid(row=0, columnspan=3, sticky='w', pady=(0, 18))
        self.status = tk.StringVar(value='Öppna en bild för att börja.')
        self.image_label = tk.StringVar(value='Ingen bild vald')
        self.source_label = tk.StringVar(value='Ingen källprofil')
        self.target_label = tk.StringVar(value='Ingen profil vald')
        self.operation = tk.StringVar(value='Konvertera till profil')
        self.mode = tk.StringVar(value='RGB')
        self.intent = tk.StringVar(value='Relativ kolorimetrisk')
        self.bpc = tk.BooleanVar(value=True)
        ttk.Button(frame, text='Öppna bild…', command=self.open_image).grid(row=1, column=0, sticky='w', pady=8)
        ttk.Label(frame, textvariable=self.image_label, wraplength=470).grid(row=1, column=1, columnspan=2, sticky='w')
        ttk.Button(frame, text='Välj källprofil…', command=lambda: self.choose_profile(True)).grid(row=2, column=0, sticky='w', pady=8)
        ttk.Label(frame, textvariable=self.source_label, wraplength=470).grid(row=2, column=1, columnspan=2, sticky='w')
        ttk.Button(frame, text='Välj målprofil…', command=lambda: self.choose_profile(False)).grid(row=3, column=0, sticky='w', pady=8)
        ttk.Label(frame, textvariable=self.target_label, wraplength=470).grid(row=3, column=1, columnspan=2, sticky='w')
        for row, label, variable, values in [(4, 'Åtgärd', self.operation, ['Konvertera till profil', 'Tilldela profil']), (5, 'Färgrymd', self.mode, list(MODES)), (6, 'Återgivningsmetod', self.intent, list(INTENTS))]:
            ttk.Label(frame, text=label).grid(row=row, column=0, sticky='w', pady=10)
            widget = ttk.Combobox(frame, textvariable=variable, values=values, state='readonly', width=30)
            widget.grid(row=row, column=1, sticky='w')
            if row == 6:
                self.intent_widget = widget
        self.bpc_widget = ttk.Checkbutton(frame, text='Svartpunktskompensation (Black Point Compensation)', variable=self.bpc)
        self.bpc_widget.grid(row=7, columnspan=3, sticky='w', pady=10)
        ttk.Label(frame, text='Utan inbäddad profil: välj först en källprofil för konvertering,\neller välj Tilldela profil för att enbart bädda in vald målprofil.', wraplength=660).grid(row=8, columnspan=3, sticky='w', pady=10)
        self.save_button = ttk.Button(frame, text='Bearbeta och spara som…', command=self.save)
        self.save_button.grid(row=9, columnspan=3, sticky='w', pady=12)
        ttk.Label(frame, textvariable=self.status, wraplength=660).grid(row=10, columnspan=3, sticky='w')
        self.operation.trace_add('write', self.update_controls)

    def update_controls(self, *_):
        state = 'disabled' if self.operation.get() == 'Tilldela profil' else 'readonly'
        self.intent_widget.configure(state=state)
        self.bpc_widget.configure(state='disabled' if state == 'disabled' else 'normal')

    def open_image(self):
        path = filedialog.askopenfilename(title='Öppna bild', filetypes=[('Bilder', '*.tif *.tiff *.jpg *.jpeg *.png'), ('Alla filer', '*')])
        if not path:
            return
        try:
            with Image.open(path) as opened:
                if getattr(opened, 'n_frames', 1) != 1:
                    raise ValueError('Bilder med flera sidor eller bildrutor stöds inte.')
                opened.load()
                image = opened.copy()
            embedded = image.info.get('icc_profile')
            source = ImageCms.ImageCmsProfile(io.BytesIO(embedded)) if embedded else None
            self.image, self.path, self.source = image, path, source
            self.image_label.set(f'{Path(path).name} · {image.width} × {image.height} · {image.mode}')
            self.source_label.set(ImageCms.getProfileDescription(source).strip() if source else 'Saknas — välj källprofil eller tilldela profil')
            self.status.set('Bilden är inläst. Originalfilen bevaras.')
        except Exception as error:
            messagebox.showerror('Kunde inte öppna bilden', str(error))

    def choose_profile(self, source):
        path = filedialog.askopenfilename(title='Välj källprofil' if source else 'Välj målprofil', filetypes=[('ICC-profiler', '*.icc *.icm'), ('Alla filer', '*')])
        if not path:
            return
        try:
            profile = ImageCms.getOpenProfile(path)
            mode = profile_mode(profile)
            label = f'{Path(path).name} · {ImageCms.getProfileDescription(profile).strip()} · {mode}'
            if source:
                if self.image is not None and self.image.info.get('icc_profile'):
                    raise ValueError('Bilden har redan en inbäddad källprofil. Den används vid konverteringen.')
                self.source = profile
                self.source_label.set(label)
            else:
                self.target = profile
                self.target_label.set(label)
                self.mode.set(next(key for key, value in MODES.items() if value == mode))
        except Exception as error:
            messagebox.showerror('Kunde inte välja profil', str(error))

    def save(self):
        if self.image is None or self.target is None:
            messagebox.showerror('Saknade val', 'Öppna en bild och välj en målprofil först.')
            return
        if self.operation.get() == 'Tilldela profil' and self.image.info.get('icc_profile'):
            messagebox.showerror('Bilden har profil', 'Välj konvertering för en bild som redan har ICC-profil.')
            return
        path = filedialog.asksaveasfilename(title='Spara bearbetad bild', initialfile=Path(self.path).stem + '_icc.tif', defaultextension='.tif', filetypes=[('TIFF', '*.tif'), ('PNG', '*.png'), ('JPEG', '*.jpg')])
        if not path:
            return
        args = (self.image, self.source, self.target, MODES[self.mode.get()], INTENTS[self.intent.get()], self.bpc.get(), self.operation.get() == 'Tilldela profil')
        original = self.path
        dpi = self.image.info.get('dpi')
        self.save_button.configure(state='disabled')
        self.status.set('Bearbetar bilden…')
        def worker():
            try:
                result = process(*args)
                save_image(result, path, original, dpi)
                self.root.after(0, lambda: self.finish(path, None))
            except Exception as error:
                self.root.after(0, self.finish, None, str(error))
        threading.Thread(target=worker, daemon=True).start()

    def finish(self, path, error):
        self.save_button.configure(state='normal')
        self.status.set('Bilden kunde inte sparas.' if error else f'Sparad: {path}')
        if error:
            messagebox.showerror('Kunde inte spara', error)

if __name__ == '__main__':
    root = tk.Tk()
    App(root)
    root.mainloop()
