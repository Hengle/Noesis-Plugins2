#by Durik256
from inc_noesis import *

def registerNoesisTypes():
    handle = noesis.register("Assetto Corsa", ".kn5")
    noesis.setHandlerTypeCheck(handle, CheckType)
    noesis.setHandlerLoadModel(handle, LoadModel)
    return 1

def CheckType(data):
    return 1

def LoadModel(data, mdlList):
    bs = NoeBitStream(data)
    ctx = rapi.rpgCreateContext()
    
    bs.seek(6) #sc6969
    ver = bs.readUInt()
    print('ver:',ver)
    if ver == 6:
        bs.seek(4,1) # 0

    global materials
    texList, materials = [], []
    numTx = bs.readUInt()
    print('numTx:',numTx)
    for x in range(numTx):
        unk = bs.readUInt()
        name = readLabel(bs)
        size = bs.readUInt()
        print('unk:',unk, 'size:', size, 'name:', name)
        tx_data = bs.read(size)
        ext = None
        if tx_data[:4] == b'DDS ':
            ext = '.dds'
        elif tx_data[:4] == b'\x89PNG':
            ext = '.png'
        
        if ext:
            texList.append(rapi.loadTexByHandler(tx_data, ext))
            texList[-1].name = name

    numMat = bs.readUInt()
    print('numMat:',numMat)
    
    for x in range(numMat):
        mat_name = readLabel(bs)
        print(' mat_name:',mat_name)
        mat = NoeMaterial(mat_name, '')
        
        #p0 = readLabel(bs)
        #_p0 = bs.read('6B')
        #print(' p0:',p0, '_p0:', _p0)
        cpos = bs.tell()
        p0 = readLabel(bs)
        print('cpos:',cpos,'len(p0):',len(p0))
        
        if ver > 4:#if ver == 5:
            bs.seek(cpos + len(p0) + 10)
        else:
            skip(bs,len(p0),cpos)
        
        #elif ver == 4:
        #    skip(bs,len(p0),cpos)
        #elif ver == 6:
        #    skip(bs,len(p0),cpos,8)
        
        print('endpos:',bs.tell())
        
        numAttr = bs.readUInt()
        print(' numAttr:',numAttr)
        for x in range(numAttr):
            a_name = readLabel(bs)
            a_p = bs.read('10f')
            print('     a_name:',a_name, 'a_p:',a_p)
        numTx = bs.readUInt()
        print(' numTx:',numTx)
        for x in range(numTx):
            t_tx = readLabel(bs)
            u_tx = bs.readUInt() # id
            n_tx = readLabel(bs)
            if t_tx == "txDiffuse":
                mat.texName = n_tx
            print('     t_tx:',t_tx, 'u_tx:',u_tx,'n_tx:',n_tx)
        materials.append(mat)    
    #numFBX = bs.readUInt()
    #print('numFBX:',numFBX)
    #for x in range(numFBX):
    #n_FBX = readLabel(bs)
    #print('FBX:',FBX)
    #u = bs.read('IB')
    #print(' u:',u)
    #g_trfm = NoeMat44.fromBytes(bs.read(64)).toMat43()
    
    # read_node
    global nodes
    nodes = []
    readNode(bs)
    
    if bs.tell() < bs.getSize():
        END = readLabel(bs)
        unk = bs.read('8B')
        print('END:',END, unk)
    
    try:
        mdl = rapi.rpgConstructModel()
    except:
        mdl = NoeModel()
    
    #if nodes:
    #    nodes = rapi.multiplyBones(nodes)
    mdl.setBones(nodes)
    mdl.setModelMaterials(NoeModelMaterials(texList, materials))
    mdlList.append(mdl)
    return 1
    
def readLabel(bs):
    return bs.read(bs.readUInt()).decode('ascii', 'ignore')
    
def skip(bs,n,cpos,i=4):
    bs.seek(cpos + (int(-1 * (n/i) // 1 * -1)*i) + 4)
    
def readNode(bs, p=-1, pTrfm=None):
    global materials
    type = bs.readUInt()
    name = readLabel(bs)
    numChild = bs.readUInt()
    unk = bs.readUByte()
    index = len(nodes)
    
    if type == 1:
        trfm = NoeMat44.fromBytes(bs.read(64)).toMat43()
        if pTrfm:
            trfm *= pTrfm
        rapi.rpgSetTransform(trfm)
        nodes.append(NoeBone(index,name,trfm,None,p))
    elif type == 2:
        print('mesh_type_node:', type)
        unk = bs.read('3B')
        print('unk:', unk)
        vnum = bs.readUInt()
        print('vnum:', vnum, [bs.tell()])
        vbuf = bs.read(vnum*44)
        inum = bs.readUInt()
        print('inum:', inum, [bs.tell()])
        ibuf = bs.read(inum*2)
        mat_id = bs.readUInt()
        unk = bs.read('29B')
        print('mat_id:',mat_id,'unk:', unk)
        
        rapi.rpgSetName(name)
        rapi.rpgSetMaterial(materials[mat_id].name)
        rapi.rpgBindPositionBuffer(vbuf, noesis.RPGEODATA_FLOAT, 44)
        rapi.rpgBindUV1BufferOfs(vbuf, noesis.RPGEODATA_FLOAT, 44, 24)
        rapi.rpgCommitTriangles(ibuf, noesis.RPGEODATA_USHORT, inum, noesis.RPGEO_TRIANGLE)
        rapi.rpgClearBufferBinds()
        
        index = p
        trfm = pTrfm
    else:
        print('error_type_node:', type)
        
    for x in range(numChild):
        readNode(bs, index, trfm)