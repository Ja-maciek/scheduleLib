# available under the MIT license, as stated in https://github.com/Ja-maciek/scheduleLib/blob/main/LICENSE

from datetime import datetime, timezone
from random import randint
import os, json, re, glob


class Schedule():
    def __init__(self, allowedEventModes=["b", "l", "s", "r", "y", "m"]): # bell, local, Spotify, radio, youtube, mic
        '''
        An object created from the class >Schedule()< can store a single, one week long series of timed events. Each event contains its timestamp, mode, parameters, sampleName and unique randomly generated eventID.\n\n

        >allowedEventModes< - set of recognised event modes
        '''
        self.eventSchedule = [[], [], []] # [[timestamp], [eventDsc], [eventID]]
        self.jsonTimings = ""
        self.allowedEventModes = allowedEventModes

        crrntTime = datetime.now(timezone.utc)
        self.prevTimestamp = crrntTime.weekday()*100000 + crrntTime.hour*3600 + crrntTime.minute*60 + crrntTime.second


    def encodeSafeEventDSC(self, text: str):
        text = text.replace("\\", "\\\\")
        if(":" in text):
            text = text.replace(":", "\\?")
        
        return text
    

    def decodeSafeEventDSC(self, text: str):
        if("\\?" in text):
            text = text.replace("\\?", ":")
        text = text.replace("\\\\", "\\")
        
        return text


    def tick(self):
        '''
        Checks if since creation of the >Schedule()< object or the last >tick()< any event should have been executed.\n\n

        Returns a list of (eventTimestamp, [eventMode, eventParams, eventSampleName], eventID) touples for the found events.
        '''
        crrntTime = datetime.now(timezone.utc)
        crrntTimestamp = crrntTime.weekday()*100000 + crrntTime.hour*3600 + crrntTime.minute*60 + crrntTime.second

        toExecute = []
        for ev in enumerate(self.eventSchedule[0]):
            if(ev[1]>self.prevTimestamp and ev[1]<=crrntTimestamp):
                toExecute.append((ev[1], [self.decodeSafeEventDSC(t) for t in self.eventSchedule[1][ev[0]].split(":")], self.eventSchedule[2][ev[0]]))
        
        self.prevTimestamp = crrntTimestamp
        return toExecute


    def add(self, timestamp: int, mode: str, params: str ="", sampleName: str =""):
        '''
        Adds the specified event to the schedule.\n\n

        >timestamp< - a timestamp being the number of seconds strating from midnight + day-of-a-week-id multipied by 100000, where in determining the day-of-a-week-id weekdays are assigned with numbers: Monday - 0 through Sunday - 6\n
        >mode< - a type of event, like playing a bell sound, local music files, streaming radio or broadcasting live microphone input; ValueError is thrown if >mode< is not in >self.allowedEventModes<\n
        >params< - a series of one-letter tags descibing settings for a sound player, like 'loop', 'shuffle', 'duration'; After each letter a numerical value of the parameter can be passed, as follows: "l10ps" - meaning: 'loop 10 times', 'playlist', 'shuffle'\n
        >sampleName< - a source descriptor (name of a bell sample, local sound file name, name of an online radio etc.)\n\n\n

        Returns (int) id of the newly created event.
        '''
        if(not (mode in self.allowedEventModes)):
            raise ValueError(f"Event mode not allowed ( {mode} ).")
        
        params = self.encodeSafeEventDSC(params)
        sampleName = self.encodeSafeEventDSC(sampleName)

        self.eventSchedule[0].append(timestamp)
        self.eventSchedule[1].append(f"{mode}:{params}:{sampleName}")

        n = 1
        newEventID = randint(10000, 99999)
        while(newEventID in self.eventSchedule[2]):
            newEventID = randint(10000, 99999)
            n += 1

            if(n > 100):
                i = 0
                while(i in self.eventSchedule[2]):
                    i += 1
                newEventID = i
                break

        self.eventSchedule[2].append(newEventID)

        return newEventID


    def remove(self, eventID: int):
        '''
        Removes the event with provided eventID.
        '''
        rmID = self.eventSchedule[2].index(eventID)
        self.eventSchedule[0].pop(rmID)
        self.eventSchedule[1].pop(rmID)
        self.eventSchedule[2].pop(rmID)
    

    def getEvent(self, eventID: int =None, eventTimestamp: int =None, eventDscRegex: str =None):
        '''
        Finds the first matching event with specified eventID or timestamp. 
        If given no id or timestamp finds all events matching the regular expression.\n\n

        Returns a list of (eventTimestamp, [eventMode, eventParams, eventSampleName], eventID) touples for the found events. 
        If no event is found or none of the parameters is passed, 
        returns None or an empty list.
        '''
        if(eventID and (eventID in self.eventSchedule[2])):
            evN = self.eventSchedule[2].index(eventID)
            return [(self.eventSchedule[0][evN], [self.decodeSafeEventDSC(t) for t in self.eventSchedule[1][evN].split(":")], self.eventSchedule[2][evN])]
        elif(eventTimestamp and (eventTimestamp in self.eventSchedule[0])):
            evN = self.eventSchedule[0].index(eventTimestamp)
            return [(self.eventSchedule[0][evN], [self.decodeSafeEventDSC(t) for t in self.eventSchedule[1][evN].split(":")], self.eventSchedule[2][evN])]
        elif(eventDscRegex):
            r = []
            for eN in range(len(self.eventSchedule[0])):
                if(re.search(eventDscRegex, self.eventSchedule[1][eN])):
                    r.append((self.eventSchedule[0][eN], [self.decodeSafeEventDSC(t) for t in self.eventSchedule[1][eN].split(":")], self.eventSchedule[2][eN]))
            return r
        else:
            return None

    def exportTimings(self):
        '''
        Exports the scheduling data to the string variable >self.jsonTimings<.\n\n

        Returns self (this >Schedule()< object)
        '''
        self.jsonTimings = json.dumps(self.eventSchedule)
        return self
    

    def saveToFile(self, destDir: str =".", newFileName: str =None):
        '''
        Saves the value of self.jsonTimings 
        (which can be generated with >self.exportTimings()<) 
        to a text file in >destPath<, with name >newFileName<.\n\n
        
        If newFileName is not supplied or is empty, the default file name is used:\n
        "sch{i}.json",\n
        where {i} is an iterator to prevent overwriting.\n\n

        Returns value of the default Python >TextIOWrapper.write()< method.
        '''

        if(not newFileName):
            i = 0
            while(os.path.exists(os.path.join(destDir, f"sch{i}.json"))):
                i += 1
            
            newFileName = f"sch{i}.json"

        with open(os.path.join(destDir, newFileName), "w") as f:
            return f.write(self.jsonTimings)
    

    def importTimings(self):
        '''
        Imports the scheduling data from >self.jsonTimings<.
        '''
        tData = json.loads(self.jsonTimings)

        self.eventSchedule[0] = tData[0]
        self.eventSchedule[1] = tData[1]
        self.eventSchedule[2] = tData[2]
    

    def readFromFile(self, sourceDir: str =None, fileName: str =None):
        '''
        Reads timings data from a JSON file to >self.jsonTimings<.\n
        If no >fileName< is provided, uses the file matching "sch[0-9]*.json" RegEx with the newest modification date.\n\n

        Returns self (this >Schedule()< object)
        '''

        if(not fileName):
            tFileName = ["", None] # [fileName, fileModificationUNIXtimestamp]
            
            for i in glob.glob("sch[0-9]*.json", root_dir=sourceDir):
                tTS = os.path.getmtime(i)
                if(tFileName[1]==None or tTS>tFileName[1]):
                    tFileName = [i, tTS]

            
            fileName = tFileName[0]

        with open(os.path.join((sourceDir if sourceDir else "."), fileName), "r") as f:
            self.jsonTimings = f.read()
        
        return self
