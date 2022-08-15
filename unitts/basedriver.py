import os
import time
from traceback import print_exc
from unitts.voice import Voice
from appPublic.background import Background
from text2sentences import text_to_sentences

class BaseDriver:
	def __init__(self, proxy):
		self._proxy = proxy
		self._tts = None
		self.sentences = []
		self.normal_voice = {}
		self.dialog_voice = {}
		self.pitch = 5
		self.language = 'zh'
		self.format = 3
		self.voice = 0
		self.cmds = []
		self._completed = True
		self.running = True
		self.task = None

	def backtask(self):
		print('player back task running ...')
		self.running = True
		while self.running:
			self._pump()
			time.sleep(0.01)
		print('player back task end ...')

	
	def speak_finish(self):
		self._proxy.notify('finished-sentence')

	def _push(self, cmd):
		self.cmds.append(cmd)

	def _pump(self):
		if self.player.is_busy():
			# print('player is busy')
			return False
		if len(self.cmds) < 1:
			# print('No cmd to do')
			if self._proxy.isBusy():
				self._proxy.setBusy(False)
				self._proxy.notify('finished-text')
			return False

		pos, fn = self.cmds.pop(0)
		self.player.set_source(fn)
		self.player.play()
		print('play ...', fn)
		self._proxy.notify('started-sentence', pos)
		return True

	def destroy(self):
		self.player.unload()
		if self.task:
			self.running = False
			self.task.join()
	
	def __del__(self):
		self.destroy()

	def startLoop(self, *args):
		print('startLoop() called')
		self._proxy.setBusy(False)
		self.task = Background(self.backtask)
		self.task.start()

	def endLoop(self):
		print('endLoop() called')
		self.cmds = []
		self._proxy.setBusy(False)
		if self.task:
			self.running = False
			self.task.join()
			self.task = None

	def set_type_voice(self, attrs, sentence):
		y = self._tts
		y.tts_set_rate(attrs.get('rate', self.rate))
		y.tts_set_pitch(attrs.get('pitch', self.pitch))
		y.tts_set_voice(attrs.get('voice', self.voice))

	def get_audio_file(self, sentence):
		y = self._tts
		if sentence.dialog:
			self.set_type_voice(self.dialog_voice, sentence)
		else:
			self.set_type_voice(self.normal_voice, sentence)
		y.tts_set_format(self.format)
		# y.tts_set_language(sentence.lang)
		raw = y.tts(sentence.text)
		if raw is None:
			print('baidu api error')
			return
		mp3file = write_tmp_mp3file(raw)
		self._push((sentence.start_pos, mp3file))
		return mp3file
		
	def say(self, sentence):
		try:
			print('baidu_d_tts driver,say() called')
			self._proxy.setBusy(False)
			self._completed = True
			mp3file = self.get_audio_file(sentence)

		except Exception as e:
			print('error:', e)
			print_exc()

	def stop(self):
		if self._proxy.isBusy():
			self._completed = False
		self.player.stop()

	def getProperty(self, name):
		if name == 'normal_voice':
			return self.normal_voice
		if name == 'dialog_voice':
			return self.dialog_voice

		if name == 'voices':
			return Voices

		if name == 'voice':
			for v in Voices:
				if v.id == self.voice:
					return v
			return None
		if name == 'rate':
			return self.rate
		if name == 'volume':
			return self.volume
		if name == 'pitch':
			return self.pitch
	
	def setProperty(self, name, value):
		if name == 'normal_voice':
			self.normal_voice = value
		if name == 'dialog_voice':
			self.dialog_voice = value
		if name == 'voice':
			self.voice = value
		if name == 'rate':
			self.rate = value
		if name == 'pitch':
			self.rate = value
		if name == 'language':
			self.language = value
		if name == 'volume':
			self.volume = value

