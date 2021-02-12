import argparse, sys

parser = argparse.ArgumentParser(description="Duo fitting input iterator")
parser.add_argument(
    'input', metavar='duo_output.out', type=str,
    help="Reference file to generate new input from."
    )
parser.add_argument(
    '-o', '--output', metavar='my_input.inp', type=str,
    help="Name of the Duo '.inp' file to write output to, if not console." 
)

args = parser.parse_args()

class fileBlock:
    def __init__(self, start_line, init_lines=[]):
        self.lines = init_lines
        self.start_line = start_line

    @property
    def line_nums(self):
        return range(self.start_line, self.start_line+len(self.lines)+1)

class objBlock(fileBlock):

    @property
    def glob_param_line_nums(self):
        for num, line in enumerate(self.lines):
            if line.split()[0].upper() == 'VALUES':
                glob_param_line_nums = range(self.start_line + num + 1, self.start_line + len(self.lines)-1)
                return list(glob_param_line_nums)
        return None
    
    @property
    def loc_param_line_nums(self):
        for num, line in enumerate(self.lines):
            if line.split()[0].upper() == 'VALUES':
                loc_param_line_nums = range(num + 1, len(self.lines))
                return list(loc_param_line_nums)
        return None

    @property
    def param_lines(self):
        return [self.lines[i] for i in self.loc_param_line_nums]


class Generator:

    object_type_ids = {
        "POTEN": 1,
        "SPIN-ORBIT": 2,
        "L2": 3,
        "LXLY": 4,
        "SPIN-SPIN": 5,
        "SPINSPIN-O": 6,
        "BOB-ROT": 7,
        "BOBROT" : 7,
        "SPIN-ROT": 8,
        "DIABATIC": 9,
        "LAMBDA-OPQ": 10,
        "LAMBDA-P2Q": 11,
        "LAMBDA-Q": 12,
        "QUADRUPOLE": 13,
        "ABINITIO": 14,
        "BROT": 15,
        "DIPOLE": 16
        }

    def __init__(self, read_file):
        self.count_id         = 0
        self.input_transcript = fileBlock(39)
        self.input_objects    = {}
        self.iter_objects     = []
        self.waiting          = {}
        self.working          = {"triggers" : (self._check_triggers, {})}
        self.triggers = {
            "(Transcript of the input --->)" : [self._read_input_transcript],
            "Parameters:" : [ self._add_new_iteration, self._read_fitting_parameters]
        }
        self.read_file = read_file
        with open(read_file, "r") as f:
            for num, line_ in enumerate(f):
                pop_ids = []
                line = line_.rstrip('\n')
                for id_ in self.working:
                    f = self.working[id_][0]
                    kwargs = self.working[id_][1]
                    done = f(num, line, **kwargs)
                    if done:
                        pop_ids.append(id_)
                [self.working.pop(id_) for id_ in pop_ids]
                for id_ in self.waiting:
                    self.working[id_] = self.waiting[id_]
                self.waiting = {}

    def genfromit(self, it_num=-1):
        for num, line in enumerate(self.input_transcript.lines):
            for obj_id, obj in self.iter_objects[it_num].items():
                if (num not in self.input_objects[obj_id].glob_param_line_nums):
                    continue
                else:
                    prev_value = line.split()[1]
                    new_line = obj.param_lines[num - self.input_objects[obj_id].glob_param_line_nums[0]]
                    line = "{0}  ({1: .21E})".format(new_line, float(prev_value))
            yield line
    
    def _read_input_transcript(self, num, line):
        if line == "(<--- End of the input.)":
            return True
        else:
            self.input_transcript.lines.append(line)
            if any(obj in line.upper() for obj in self.object_type_ids):
                obj_id = self._determine_id(line)
                self.input_objects[obj_id] = objBlock(num-self.input_transcript.start_line, init_lines=[line])
                self._new_waiting(self._read_input_objects, {'obj_id' : obj_id})
            return False

    def _read_fitting_parameters(self, num, line):
        if line == "Fitted paramters (rounded):":
            return True
        else:
            if any(obj in line.upper() for obj in self.object_type_ids):
                obj_id = self._determine_id(line)
                self.iter_objects[-1][obj_id] = objBlock(num, init_lines=[line])
                self._new_waiting(self._read_fitting_objects, {'obj_id' : obj_id})
    
    def _add_new_iteration(self, num, line):
        self.iter_objects.append({})
        return True

    def _check_triggers(self, num, line):
        if line in self.triggers:
            for f in self.triggers[line]:
                self._new_waiting(f, {})
            return False
        else:
            return False
    
    def _read_input_objects(self, num, line, obj_id=None):
        self.input_objects[obj_id].lines.append(line)
        if line.strip().upper() == "END":
            return True
        else:
            return False
    
    def _read_fitting_objects(self, num, line, obj_id=None):
        self.iter_objects[-1][obj_id].lines.append(line)
        if line.strip().upper() == "END":
            return True
        else:
            return False

    def _determine_id(self, line):
        keys = line.upper().split()
        obj_type = self.object_type_ids[keys[0]]
        if obj_type == 14:
            abinitio = True
            obj_type = self.object_type_ids[keys[1]]
            keys = keys[1:]
        else:
            abinitio = False
        if obj_type == 1:
            l_id = r_id = int(keys[1])
        else:
            l_id, r_id = int(keys[1]), int(keys[2])
        obj_id = (abinitio, obj_type, l_id, r_id)
        return obj_id
    
    def _new_waiting(self, func, kwargs):   
        self.count_id += 1
        self.waiting[str(self.count_id)] = (func, kwargs)

gen = Generator(args.input)
if args.output is not None:
    fout = open(args.output, 'w+')
    fout.close
    for line in gen.genfromit():
        fout = open(args.output, 'a')
        print(line, file=fout)
        fout.close()
else:
    fout = sys.stdout
    for line in gen.genfromit():
        print(line, file=fout)

