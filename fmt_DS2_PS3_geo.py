#by Durik256
from inc_noesis import *

def registerNoesisTypes():
    handle = noesis.register("Dead Space 2 PS3", ".geo")
    noesis.setHandlerTypeCheck(handle, noepyCheckType)
    noesis.setHandlerLoadModel(handle, noepyLoadModel)
    return 1

def noepyCheckType(data):
    if data[:4] != b'EAGM': 
        return 0
    return 1   
    
def noepyLoadModel(data, mdlList): 
    ctx = rapi.rpgCreateContext()        

    bs = NoeBitStream(data, 1)
    rapi.rpgSetEndian(1)
    
    uvPath, uvbuf = find_uv_file(), None
    if uvPath and rapi.checkFileExists(uvPath):
        uvbuf = rapi.loadIntoByteArray(uvPath)
    print('uvPath:', uvPath)
    
    bs.seek(62)
    submesh =  bs.readShort()
    print("count submesh:", submesh)
    bs.seek(104) 
    
    vTableOff = bs.readUInt() 
    print("vTableOff:", vTableOff)
    fTableOff = bs.readUInt() 
    print("fTableOff:", fTableOff)
    
    #vertex
    bs.seek(vTableOff)
    vertex_inf = []
    uvs_inf = []
    for x in range(submesh):
        _ = list(bs.read('>2IH2BI'))
        if not _[5]: _[5] = vTableOff + 128
        vertex_inf.append(_)
        print("Vsize:", _[0], "Vcount:", _[1], "Vstride:", _[2], "Vtype:", _[3], "Vflag:", _[4], "VStart:", _[5])

        #uvs
        #bs.seek(16,1)
        _ = list(bs.read('>2IH2BI'))
        uvs_inf.append(_)
        print("    UVsize:", _[0], "UVcount:", _[1], "UVstride:", _[2], "UVtype:", _[3], "UVflag:", _[4], "UVStart:", _[5])

    #face
    bs.seek(fTableOff)
    face_inf = []
    for x in range(submesh):
        _ = bs.read('>2IH2BI')
        face_inf.append(_)
        print("FBsize:", _[0], "FCount:", _[1], "Fstride:", _[2], "Ftype:", _[3], "Fflag:", _[4], "FStart:", _[5])

    for x in range(submesh): 
        rapi.rpgSetName('mesh_%i'%x)
        
        Vsize, VCount, Vstride, Vtype, Vflag, VStart = vertex_inf[x]
        UVsize, UVCount, UVstride, UVtype, UVflag, UVStart = uvs_inf[x]
        FBsize, FCount, Fstride, Ftype, Fflag, FStart = face_inf[x]
        
        stride = Vstride if Vflag==0 else Vstride + 12
        print("stride:",stride)
        
        bs.seek(VStart)
        VBuf = bs.readBytes(VCount * stride)
        bs.seek(FStart)
        IBuf = bs.readBytes(FBsize)

        rapi.rpgBindPositionBuffer(VBuf, noesis.RPGEODATA_FLOAT, stride)
        #uvPath = noesis.userPrompt(noesis.NOEUSERVAL_FILEPATH, "Open File", "Select UVs from 'MeshVolatile'", noesis.getSelectedFile())
        #if uvPath and rapi.checkFileExists(uvPath):
        #    uvbuf = rapi.loadIntoByteArray(uvPath)
        #    rapi.rpgBindUV1Buffer(uvbuf, noesis.RPGEODATA_FLOAT, 8) 
        if uvbuf and UVCount == VCount and UVtype == 6: #FLOAT
            _UVStart = UVStart - len(data)
            rapi.rpgBindUV1Buffer(uvbuf[_UVStart:_UVStart+UVsize], noesis.RPGEODATA_FLOAT, UVstride) 
        rapi.rpgSetPosScaleBias(NoeVec3([174, 174, 174]), None)
        
        if Ftype != 1:                                     
            rapi.rpgCommitTriangles(IBuf, noesis.RPGEODATA_SHORT, FCount, noesis.RPGEO_TRIANGLE_STRIP, 1)
        else:
            rapi.rpgCommitTriangles(IBuf, noesis.RPGEODATA_SHORT, FCount, noesis.RPGEO_TRIANGLE, 1)
        rapi.rpgClearBufferBinds()
    
    mdl = rapi.rpgConstructModel()                                                          
    mdlList.append(mdl)
    return 1
    
def find_uv_file():
    main_file_path = rapi.getInputName()

    base_dir = os.path.dirname(main_file_path)
    file_name = os.path.basename(main_file_path)
    name_no_ext = os.path.splitext(file_name)[0]

    parts = name_no_ext.split('_')
    if len(parts) >= 1:
        try:
            uv_id = int(parts[0]) + 1
            rest = "_".join(parts[1:]) if len(parts) > 1 else ""
            
            uv_folder = os.path.join(base_dir, "MeshVolatile")
            uv_path1 = os.path.join(uv_folder, "{:04d}_{}.geo".format(uv_id, rest))
            uv_path2 = os.path.join(uv_folder, "{}_{}.geo".format(uv_id, rest))
            uv_path3 = os.path.join(uv_folder, file_name)

            uv_path4 = os.path.join(base_dir, "{:04d}_{}.geo".format(uv_id, rest))
            uv_path5 = os.path.join(base_dir, "{}_{}.geo".format(uv_id, rest))
            uv_path6 = os.path.join(base_dir, file_name)
                        
            for uv_path in [uv_path1, uv_path2, uv_path3, uv_path4, uv_path5, uv_path6]:
                if os.path.exists(uv_path) and uv_path != main_file_path:
                    return uv_path
                    
        except ValueError:
            pass
    
    return None
    
'''
def noepyLoadModel(data, mdlList):
    ctx = rapi.rpgCreateContext()   
    bs = NoeBitStream(data, 1)
    rapi.rpgSetEndian(1)

    uvPath = find_uv_file()
    bs.seek(32, 1)
    
    modelName = read_name(bs, bs.readUInt())
    bs.seek(16, 1)
    
    tableCount = bs.readUInt()
    bs.seek(24, 1)

    dataTable1 = bs.readUInt()
    bs.seek(156)
    
    uvOffsetLocal = bs.readUInt()

    print("Model:", modelName)
    print("Table count:", tableCount)
    
    # Read table entries
    subMeshes = []
    bs.seek(dataTable1)
    for i in range(tableCount):
        sm = subMesh()
        sm.meshName = read_name(bs, bs.readUInt())
        bs.seek(35, 1)
        sm.uvSize = bs.readUByte()
        bs.seek(8, 1)
        sm.faceCount = bs.readUInt()
        _ = bs.readUInt()
        sm.vertCount = bs.readUShort()
        _ = bs.readUShort()
        sm.lodType = bs.readUShort()
        bs.seek(38, 1)
        sm.vertSize = bs.readInt()
        _ = bs.readUInt()
        sm.vertID = bs.readUInt()
        bs.seek(20, 1)
        sm.vertOffset = bs.readUInt()
        sm.faceOffset = bs.readUInt()
        bs.seek(52, 1)
        subMeshes.append(sm)
        
        print("Mesh :", sm.meshName, "vertOffset:", sm.vertOffset, "Verts:", sm.vertCount, "Faces:" , sm.faceCount, "VertSize:" , sm.vertSize)

    for i, sm in enumerate(subMeshes):
        for j in range(i - 1, -1, -1):
            if subMeshes[j].vertID == sm.vertID:
                sm.allVertCount += subMeshes[j].vertCount

    for i, sm in enumerate(subMeshes):
        process_mesh(bs, i, sm, uvPath, uvOffsetLocal)

    try:
        mdl = rapi.rpgConstructModel()                                           
    except:
        mdl = NoeModel()
    
    mdlList.append(mdl)
    return 1
    
def process_mesh(bs, meshIdx, sm, uvFile, uvOffsetLocal):
    print("Processing mesh", meshIdx)

    rapi.rpgSetName(sm.meshName)
    rpgeo = noesis.RPGEO_TRIANGLE_STRIP if (sm.lodType != 5) else noesis.RPGEO_TRIANGLE

    # Read vertices
    bs.seek(sm.vertOffset)
    if sm.vertSize == -1:  
        stride = 32
    else:
        if sm.lodType == 5: 
            stride = 20
        elif sm.lodType == 4: 
            stride = 12

    print("stride mesh::", stride, "lodType::", sm.lodType)
    vbuf = bs.readBytes(sm.vertCount * stride)
    rapi.rpgSetPosScaleBias(NoeVec3([174, 174, 174]), None)
    rapi.rpgBindPositionBuffer(vbuf, noesis.RPGEODATA_FLOAT, stride)
    if stride > 12:
        rapi.rpgBindNormalBufferOfs(vbuf, noesis.RPGEODATA_USHORT, stride, 12)
    
    # Read UVs
    #if uvFile:
    #    print("Using external UVs")
    #    # For simplicity, read UVs sequentially for now
    #    #for j in range(vertCount):
    #    #uvbuf = rapi.loadIntoByteArray(uvPath)
    #    #rapi.rpgBindUV1Buffer(uvbuf, noesis.RPGEODATA_FLOAT, 8) 
    #else:
    #    print("Using local UVs")
    #    curr_pos = bs.tell()
    #    bs.seek(uvOffsetLocal)
    #    
    #    uvbuf = rapi.loadIntoByteArray(vertCount * uvSize)
    #    rapi.rpgBindUV1Buffer(uvbuf, noesis.RPGEODATA_FLOAT, uvSize) 


    # Read faces
    bs.seek(sm.faceOffset)
    print('>>faceOffset:', sm.faceOffset, 'faceCount:', sm.faceCount, 'allVertCount:', sm.allVertCount)
    if not sm.allVertCount:
        ibuf = bs.readBytes(sm.faceCount * 2)
    else:
        ibuf = b''
        _ = sm.allVertCount
        for x in range(sm.faceCount):
            ibuf += noePack('>H', bs.readUShort() - _)

    rapi.rpgCommitTriangles(ibuf, noesis.RPGEODATA_USHORT, sm.faceCount, rpgeo)

    rapi.rpgClearBufferBinds()
    #print("Created mesh:" ,meshName,"with",sm.vertCount,"vertices",sm.faceCount, "indices")
    
    
def read_fixed_string(bs, size):
    string = bs.readBytes(size).decode('ASCII', errors='ignore')
    string = string.replace('\xFD', '').replace('\xFC', '')
    return string.rstrip('\x00')

def read_name(bs, offset):
    if offset == 0:
        return ""
    curr_pos = bs.tell()
    bs.seek(offset)
    name = bs.readString()
    bs.seek(curr_pos)
    return name
    
class subMesh:
    def __init__(self):
        self.meshName = ''
        self.allVertCount = 0
        self.vertCount = 0
        self.vertSize = 0
        self.vertOffset = 0
        self.vertID = 0
        self.uvSize = 0
        self.faceOffset = 0
        self.faceCount = 0
        self.lodType = 0
'''
