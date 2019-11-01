from PyQt5.QtWidgets import QTimeEdit


class FiveMinuteTimeEdit(QTimeEdit):
    def stepBy(self, steps):
        if self.currentSection() == self.MinuteSection:
            QTimeEdit.stepBy(self, steps * 5)
        else:
            QTimeEdit.stepBy(self, steps)


# class myTime : public QTimeEdit
# {
#     Q_OBJECT
# public:
#     virtual void stepBy(int steps)
#     {
#         if (this->time().minute()==59 && steps>0){
#             setTime(QTime(time().hour()+1,0,time().second(),time().msec()));
#         }else if(this->time().minute()==00 && steps<0){
#             setTime(QTime(time().hour()-1,59,time().second(),time().msec()));
#         }else{
#             QTimeEdit::stepBy(steps);
#         }
#     }
# };
