import secrets # Kriptografik olarak güvenli rasgele sayılar ve seçimler için (Eleştiri 1)
import string

def run_action(parameters):
    """
    Belirtilen kriterlere göre rasgele bir parola üretir, kriptografik güvenliği sağlar
    ve seçilen karakter tipleri için minimum karmaşıklığı zorunlu kılar.

    Parameters:
    parameters (dict): Aşağıdaki anahtarları içeren bir sözlük:
        'length' (int): Parolanın istenen uzunluğu. Varsayılan olarak 12.
        'include_uppercase' (bool, optional): True ise, büyük harfleri içerir. Varsayılan olarak True.
        'include_lowercase' (bool, optional): True ise, küçük harfleri içerir. Varsayılan olarak True.
        'include_digits' (bool, optional): True ise, rakamları (0-9) içerir. Varsayılan olarak True.
        'include_symbols' (bool, optional): True ise, özel sembolleri içerir. Varsayılan olarak True.
        'custom_symbols' (str, optional): İçerilecek özel sembollerin bir dizesi.
                                          Sağlanırsa ve 'include_symbols' True ise,
                                          bu semboller varsayılan `string.punctuation` yerine kullanılır.

    Returns:
    str: Rasgele oluşturulmuş bir parola.

    Raises:
    ValueError: Parola uzunluğu pozitif bir tamsayı değilse,
                hiçbir karakter türü seçilmemişse veya
                belirtilen kriterlere göre karakter mevcut değilse.
    """
    length = parameters.get('length', 12)
    include_uppercase = parameters.get('include_uppercase', True)
    include_lowercase = parameters.get('include_lowercase', True)
    include_digits = parameters.get('include_digits', True)
    include_symbols = parameters.get('include_symbols', True)
    custom_symbols = parameters.get('custom_symbols', None)

    if not isinstance(length, int) or length <= 0:
        raise ValueError("Password length must be a positive integer.")

    # Tüm olası karakterleri tutacak bir liste (Eleştiri 3 - performans)
    # Dize birleştirmeyi tek seferde yapmak için listeye eklenir.
    all_possible_characters_pool_list = []
    # Parolada en az bir tane bulunması garanti edilecek karakter setleri (Eleştiri 2 - güvenlik/karmaşıklık)
    guaranteed_character_types = []

    if include_uppercase:
        all_possible_characters_pool_list.append(string.ascii_uppercase)
        guaranteed_character_types.append(string.ascii_uppercase)
    if include_lowercase:
        all_possible_characters_pool_list.append(string.ascii_lowercase)
        guaranteed_character_types.append(string.ascii_lowercase)
    if include_digits:
        all_possible_characters_pool_list.append(string.digits)
        guaranteed_character_types.append(string.digits)
    if include_symbols:
        symbols_to_use = custom_symbols if custom_symbols is not None else string.punctuation
        if symbols_to_use: # Sembol seti boş değilse ekle
            all_possible_characters_pool_list.append(symbols_to_use)
            guaranteed_character_types.append(symbols_to_use)
        # Eğer custom_symbols boş bir string ise ve başka karakter tipi yoksa, aşağıdaki kontroller bunu yakalayacaktır.

    # Tüm olası karakter havuzunu tek bir dize olarak birleştir (Eleştiri 3 - performans)
    all_possible_characters = "".join(all_possible_characters_pool_list)

    if not all_possible_characters:
        raise ValueError("No characters available to generate password with specified criteria. "
                         "At least one character type (uppercase, lowercase, digits, symbols) must be included. "
                         "If 'include_symbols' is True and 'custom_symbols' is provided, "
                         "'custom_symbols' must not be an empty string if it's the only type selected.")

    if not guaranteed_character_types:
        # Bu durum zaten yukarıdaki `if not all_possible_characters:` tarafından yakalanmalıdır,
        # ancak daha net bir hata mesajı için burada tutulabilir.
        raise ValueError("At least one character type (uppercase, lowercase, digits, symbols) must be included.")

    password_characters = []

    # 1. Seçilen her türden en az bir karakterin parolada bulunmasını sağla (Eleştiri 2)
    # Bu, parolanın belirtilen türlerde minimum karmaşıklığa sahip olmasını garanti eder.
    for char_set in guaranteed_character_types:
        if len(password_characters) < length: # Sadece parola uzunluğu izin veriyorsa ekle
            password_characters.append(secrets.choice(char_set)) # Eleştiri 1 - secrets modülü kullanıldı
        else:
            break # Parola uzunluğu garanti edilen karakterlerle dolu veya aşıldı

    # 2. Parolanın geri kalanını, tüm olası karakter havuzundan rasgele karakterlerle doldur (Eleştiri 1)
    while len(password_characters) < length:
        password_characters.append(secrets.choice(all_possible_characters))

    # 3. Karakterlerin konumlarındaki rasgeleliği sağlamak için parolayı karıştır (Eleştiri 2)
    # secrets.SystemRandom() kriptografik olarak güvenli rasgelelik sağlayan bir nesnedir
    # ve kendi shuffle metoduna sahiptir.
    secrets.SystemRandom().shuffle(password_characters) 

    return "".join(password_characters)

TOOL_NAME: password_generator