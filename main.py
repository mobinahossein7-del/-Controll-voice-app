# ============================================================
# Voice Control
# Arabic Voice Recognition for Android
# ============================================================

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.core.text import LabelBase
from kivy.clock import Clock


# ============================================================
# Arabic Font
# ============================================================

FONT_FILE = "NotoKufiArabic-VariableFont_wght.ttf"

try:
    LabelBase.register(
        name="Arabic",
        fn_regular=FONT_FILE
    )
    ARABIC_FONT = "Arabic"
except Exception:
    ARABIC_FONT = "Roboto"


# ============================================================
# Android UI Thread
# ============================================================

try:
    from android.runnable import run_on_ui_thread
except Exception:

    def run_on_ui_thread(func):
        return func


# ============================================================
# Voice Control App
# ============================================================

class VoiceControlApp(App):

    def build(self):

        self.title = "التحكم الصوتي"

        self.recognizer = None
        self.listener = None

        # ----------------------------------------------------
        # Main Layout
        # ----------------------------------------------------

        layout = BoxLayout(
            orientation="vertical",
            padding=30,
            spacing=20
        )

        # ----------------------------------------------------
        # Title
        # ----------------------------------------------------

        self.title_label = Label(
            text="التحكم الصوتي بالإعدادات",
            font_name=ARABIC_FONT,
            font_size=26,
            halign="center",
            valign="middle",
            size_hint_y=None,
            height=90
        )

        layout.add_widget(
            self.title_label
        )

        # ----------------------------------------------------
        # Status
        # ----------------------------------------------------

        self.status_label = Label(
            text="اضغط على زر بدء الاستماع",
            font_name=ARABIC_FONT,
            font_size=20,
            halign="center",
            valign="middle"
        )

        layout.add_widget(
            self.status_label
        )

        # ----------------------------------------------------
        # Recognized Text
        # ----------------------------------------------------

        self.result_label = Label(
            text="",
            font_name=ARABIC_FONT,
            font_size=19,
            halign="center",
            valign="middle"
        )

        layout.add_widget(
            self.result_label
        )

        # ----------------------------------------------------
        # Start Button
        # ----------------------------------------------------

        start_button = Button(
            text="🎤 بدء الاستماع",
            font_name=ARABIC_FONT,
            font_size=22,
            size_hint_y=None,
            height=75
        )

        start_button.bind(
            on_release=self.start_listening
        )

        layout.add_widget(
            start_button
        )

        # ----------------------------------------------------
        # Stop Button
        # ----------------------------------------------------

        stop_button = Button(
            text="إيقاف الاستماع",
            font_name=ARABIC_FONT,
            font_size=20,
            size_hint_y=None,
            height=65
        )

        stop_button.bind(
            on_release=self.stop_listening
        )

        layout.add_widget(
            stop_button
        )

        # ----------------------------------------------------
        # Clear Button
        # ----------------------------------------------------

        clear_button = Button(
            text="مسح النص",
            font_name=ARABIC_FONT,
            font_size=20,
            size_hint_y=None,
            height=65
        )

        clear_button.bind(
            on_release=self.clear_text
        )

        layout.add_widget(
            clear_button
        )

        return layout


    # ========================================================
    # Update UI safely
    # ========================================================

    def set_status(self, text):

        Clock.schedule_once(
            lambda dt: self._set_status(text),
            0
        )


    def _set_status(self, text):

        self.status_label.text = text


    def set_result(self, text):

        Clock.schedule_once(
            lambda dt: self._set_result(text),
            0
        )


    def _set_result(self, text):

        self.result_label.text = text


    # ========================================================
    # Start Listening
    #
    # IMPORTANT:
    # SpeechRecognizer must be created and started
    # from Android Main Thread.
    # ========================================================

    @run_on_ui_thread
    def start_listening(self, *args):

        try:

            # ------------------------------------------------
            # Android classes
            # ------------------------------------------------

            from jnius import autoclass
            from jnius import PythonJavaClass
            from jnius import java_method

            PythonActivity = autoclass(
                "org.kivy.android.PythonActivity"
            )

            SpeechRecognizer = autoclass(
                "android.speech.SpeechRecognizer"
            )

            RecognizerIntent = autoclass(
                "android.speech.RecognizerIntent"
            )

            Intent = autoclass(
                "android.content.Intent"
            )

            activity = PythonActivity.mActivity

            # ------------------------------------------------
            # Check Speech Recognition
            # ------------------------------------------------

            if not SpeechRecognizer.isRecognitionAvailable(
                activity
            ):

                self.set_status(
                    "التعرف الصوتي غير متوفر على الجهاز"
                )

                return

            # ------------------------------------------------
            # Stop old recognizer if it exists
            # ------------------------------------------------

            try:

                if self.recognizer is not None:

                    self.recognizer.stopListening()

                    self.recognizer.cancel()

                    self.recognizer.destroy()

            except Exception:
                pass

            self.recognizer = None
            self.listener = None

            # ------------------------------------------------
            # Recognition Listener
            # ------------------------------------------------

            app = self


            class RecognitionListener(
                PythonJavaClass
            ):

                __javainterfaces__ = [
                    "android.speech.RecognitionListener"
                ]

                __javacontext__ = "app"


                def __init__(self):

                    super().__init__()


                # --------------------------------------------
                # Ready
                # --------------------------------------------

                @java_method("(Landroid/os/Bundle;)V")
                def onReadyForSpeech(self, params):

                    app.set_status(
                        "جاهز للاستماع..."
                    )


                # --------------------------------------------
                # Beginning of speech
                # --------------------------------------------

                @java_method("()V")
                def onBeginningOfSpeech(self):

                    app.set_status(
                        "🎤 أستمع إليك..."
                    )


                # --------------------------------------------
                # Buffer
                # --------------------------------------------

                @java_method("([B)V")
                def onBufferReceived(self, buffer):

                    pass


                # --------------------------------------------
                # End of speech
                # --------------------------------------------

                @java_method("()V")
                def onEndOfSpeech(self):

                    app.set_status(
                        "جارٍ معالجة الكلام..."
                    )


                # --------------------------------------------
                # Error
                # --------------------------------------------

                @java_method("(I)V")
                def onError(self, error):

                    messages = {

                        1: "خطأ في الشبكة",

                        2: "الشبكة غير متوفرة",

                        3: "الخادم مشغول",

                        4: "الخدمة غير متاحة",

                        5: "خطأ في العميل",

                        6: "لم يبدأ الكلام",

                        7: "لم يتم العثور على كلام",

                        8: "انتهت مهلة التعرف",

                        9: "الصلاحية غير متوفرة"

                    }

                    message = messages.get(
                        error,
                        "حدث خطأ في التعرف الصوتي"
                    )

                    app.set_status(
                        message
                    )


                # --------------------------------------------
                # Partial Results
                # --------------------------------------------

                @java_method(
                    "(Landroid/os/Bundle;)V"
                )
                def onPartialResults(
                    self,
                    results
                ):

                    app.read_results(
                        results,
                        False
                    )


                # --------------------------------------------
                # Final Results
                # --------------------------------------------

                @java_method(
                    "(Landroid/os/Bundle;)V"
                )
                def onResults(
                    self,
                    results
                ):

                    app.read_results(
                        results,
                        True
                    )


                # --------------------------------------------
                # RMS
                # --------------------------------------------

                @java_method("(F)V")
                def onRmsChanged(
                    self,
                    rmsdB
                ):

                    pass


                # --------------------------------------------
                # Event
                # --------------------------------------------

                @java_method(
                    "(ILandroid/os/Bundle;)V"
                )
                def onEvent(
                    self,
                    eventType,
                    params
                ):

                    pass


            # ------------------------------------------------
            # Create listener
            # ------------------------------------------------

            self.listener = RecognitionListener()

            # ------------------------------------------------
            # Create SpeechRecognizer
            #
            # This is now running on Android Main Thread.
            # ------------------------------------------------

            self.recognizer = (
                SpeechRecognizer.createSpeechRecognizer(
                    activity
                )
            )

            self.recognizer.setRecognitionListener(
                self.listener
            )

            # ------------------------------------------------
            # Recognition Intent
            # ------------------------------------------------

            intent = Intent(
                RecognizerIntent.ACTION_RECOGNIZE_SPEECH
            )

            intent.putExtra(
                RecognizerIntent.EXTRA_LANGUAGE_MODEL,
                RecognizerIntent.LANGUAGE_MODEL_FREE_FORM
            )

            # Arabic
            intent.putExtra(
                RecognizerIntent.EXTRA_LANGUAGE,
                "ar"
            )

            intent.putExtra(
                RecognizerIntent.EXTRA_LANGUAGE_PREFERENCE,
                "ar"
            )

            # Partial results
            intent.putExtra(
                RecognizerIntent.EXTRA_PARTIAL_RESULTS,
                True
            )

            # ------------------------------------------------
            # Start recognition
            # ------------------------------------------------

            self.set_status(
                "جاري بدء الاستماع..."
            )

            self.recognizer.startListening(
                intent
            )

        except Exception as e:

            self.set_status(
                "حدث خطأ أثناء تشغيل الميكروفون"
            )

            self.set_result(
                str(e)
            )


    # ========================================================
    # Read Speech Results
    # ========================================================

    def read_results(
        self,
        results,
        final_result=False
    ):

        try:

            if results is None:
                return

            ArrayList = results.getStringArrayList(
                "results_recognition"
            )

            if ArrayList is None:
                return

            if ArrayList.size() == 0:
                return

            text = str(
                ArrayList.get(0)
            )

            if not text:
                return

            # -----------------------------------------------
            # Show recognized text
            # -----------------------------------------------

            self.set_result(
                text
            )

            if final_result:

                self.set_status(
                    "تم التعرف على الأمر"
                )

                # -------------------------------------------
                # Process command
                # -------------------------------------------

                Clock.schedule_once(
                    lambda dt: self.process_command(text),
                    0
                )

            else:

                self.set_status(
                    "🎤 " + text
                )

        except Exception as e:

            self.set_result(
                str(e)
            )


    # ========================================================
    # Stop Listening
    #
    # IMPORTANT:
    # stopListening() is also executed on Main Thread.
    # ========================================================

    @run_on_ui_thread
    def stop_listening(self, *args):

        try:

            if self.recognizer is not None:

                self.recognizer.stopListening()

                self.recognizer.cancel()

                self.recognizer.destroy()

                self.recognizer = None

                self.listener = None

            self.set_status(
                "تم إيقاف الاستماع"
            )

        except Exception as e:

            self.set_status(
                "تم إيقاف الاستماع"
            )


    # ========================================================
    # Process Voice Command
    # ========================================================

    def process_command(self, text):

        command = text.strip().lower()

        # ----------------------------------------------------
        # Wi-Fi
        # ----------------------------------------------------

        if (
           
